import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { StateService } from '../../services/state.service';

import {
  SlideContent,
  LAYOUT_HINTS,
  ImageCandidate,
  ConfirmOutlineRequest,
  Presentation,
  OutlineResponse,
  Palette
} from '../../models/presentation.models';

import { Select } from 'primeng/select';
import { Textarea } from 'primeng/textarea';
import { InputText } from 'primeng/inputtext';
import {PrimeTemplate} from "primeng/api";
import {Button} from "primeng/button";

@Component({
  selector: 'app-outline',
  standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        Select,
        Textarea,
        InputText,
        PrimeTemplate,
        Button
    ],
  templateUrl: './outline.component.html',
  styleUrl: './outline.component.css'
})
export class OutlineComponent implements OnInit {

  private api = inject(ApiService);
  state = inject(StateService);

  title = '';
  subtitle = '';

  presenters: string[] = [];
  date: string | null = null;

  slides: SlideContent[] = [];
  palettes: Palette[] = [];
  selectedPaletteIndex = 0;

  palette: Record<string, string> = {};

  layoutHints = [...LAYOUT_HINTS] as any[];

  loading = false;
  error = '';
  progress = '';

  ngOnInit() {
    const outline = this.state.outline();

    if (!outline) {
      this.state.goTo(1);
      return;
    }

    this.title = outline.title || '';
    this.subtitle = outline.subtitle || '';
    this.presenters = outline.presenters || [];
    this.date = outline.date || null;

    this.slides = (outline.slides || []).map((slide) => ({
      ...slide,

      points: slide.points || [],
      stats: slide.stats || [],
      timeline: slide.timeline || [],

      chart: slide.chart || null,

      image_query: slide.image_query || '',

      image_selection: slide.image_selection
          ? {
            ...slide.image_selection,
            candidates: slide.image_selection.candidates || []
          }
          : null
    }));

    this.palettes = Array.isArray(outline.palettes)
      ? [...outline.palettes]
      : [];

    if (!this.palettes.length && outline.palette) {
      this.palettes = [
        {
          name: 'Default palette',
          bg: outline.palette['bg'] || '#0B1426',
          surface: outline.palette['surface'] || '#132040',
          primary: outline.palette['primary'] || '#1E3A6E',
          accent: outline.palette['accent'] || '#D4A843',
          text: outline.palette['text'] || '#F0F4FA',
          muted: outline.palette['muted'] || '#7A8BA8',
        }
      ];
    }

    const initialIndex = Number.isInteger(outline.selected_palette_index)
      ? Number(outline.selected_palette_index)
      : 0;

    this.applySelectedPalette(initialIndex, false);
    this.saveChanges();
  }

  saveChanges() {
    this.state.updateOutline({
      title: this.title.trim() || 'Presentation',

      subtitle: this.subtitle.trim(),

      presenters: this.presenters
          .map(p => p.trim())
          .filter(Boolean),

      date: this.date?.trim() || null,

      palettes: [...this.palettes],
      palette: { ...this.palette },
      selected_palette_index: this.selectedPaletteIndex,

      slides: this.slides
    });
  }
  get paletteOptions() {
    return this.palettes.map((palette, index) => ({
      label: palette.name?.trim() || `Palette ${index + 1}`,
      value: index,
      entries: Object.entries(palette).filter(
          ([key]) => key !== 'name'
      )
    }));
  }

  selectedPaletteEntries() {
    return Object.entries(this.palette).filter(
      ([key]) => key !== 'name'
    );
  }

  onPaletteChange(index: number) {
    this.applySelectedPalette(index);
  }

  private applySelectedPalette(
    index: number,
    persist = true
  ) {
    if (!this.palettes.length) {
      this.selectedPaletteIndex = 0;
      this.palette = {};

      if (persist) {
        this.saveChanges();
      }

      return;
    }

    const safeIndex = Math.max(
      0,
      Math.min(
        index,
        this.palettes.length - 1
      )
    );

    const selected = this.palettes[safeIndex];

    this.selectedPaletteIndex = safeIndex;
    this.palette = {
      name: selected.name,
      bg: selected.bg,
      surface: selected.surface,
      primary: selected.primary,
      accent: selected.accent,
      text: selected.text,
      muted: selected.muted
    };

    if (persist) {
      this.saveChanges();
    }
  }

  setPresentersFromInput(value: string) {
    this.presenters = value
        .split(',')
        .map(presenter => presenter.trim())
        .filter(Boolean);

    this.saveChanges();
  }

  selectImage(
      slide: SlideContent,
      image: ImageCandidate
  ) {
    if (!slide.image_selection) {
      return;
    }

    slide.image_selection.selected_url = image.url;

    this.saveChanges();
  }

  isImageSelected(
      slide: SlideContent,
      image: ImageCandidate
  ): boolean {
    return slide.image_selection?.selected_url === image.url;
  }

  addPoint(slide: SlideContent) {
    slide.points.push({
      point: '',
      explanation: ''
    });

    this.saveChanges();
  }

  removePoint(
      slide: SlideContent,
      index: number
  ) {
    slide.points.splice(index, 1);
    this.saveChanges();
  }

  addSlide() {
    this.slides.push({
      label: `Slide ${this.slides.length + 1}`,
      notes: '',
      objective: '',
      points: [],
      stats: [],
      chart: null,
      timeline: [],
      layout_hint: 'content',
      image_query: '',
      image_selection: null
    });

    this.saveChanges();
  }

  removeSlide(index: number) {
    this.slides.splice(index, 1);
    this.saveChanges();
  }

  back() {
    this.saveChanges();
    this.state.goTo(1);
  }

  confirm(): void {
    if (!this.slides.length) {
      this.error = 'Add at least one slide.';
      return;
    }

    this.error = '';
    this.loading = true;

    this.saveChanges();

    this.progress = `Generating ${this.slides.length} slides...`;

    const slides: SlideContent[] = this.slides.map(
        (slide): SlideContent => ({
          label: slide.label?.trim() || 'Untitled slide',

          notes: slide.notes?.trim() || '',

          objective: slide.objective?.trim() || '',

          points: (slide.points || []).map(point => ({
            point: point.point?.trim() || '',
            explanation: point.explanation?.trim() || ''
          })),

          stats: (slide.stats || []).map(stat => ({
            value: stat.value?.trim() || '',
            label: stat.label?.trim() || '',
            context: stat.context?.trim() || ''
          })),

          chart: slide.chart
              ? {
                type: slide.chart.type || 'bar',
                title: slide.chart.title?.trim() || '',
                description: slide.chart.description?.trim() || '',
                data: Array.isArray(slide.chart.data)
                    ? slide.chart.data.map((row: any) => ({
                      label: row?.label?.toString().trim() || '',
                      value: row?.value ?? ''
                    }))
                    : []
              }
              : null,

          timeline: (slide.timeline || []).map(item => ({
            period: item.period?.trim() || '',
            title: item.title?.trim() || '',
            description: item.description?.trim() || ''
          })),

          layout_hint: slide.layout_hint || 'content',

          image_query: slide.image_query?.trim() || '',

          image_selection: slide.image_selection
              ? {
                query: slide.image_selection.query || '',
                candidates: slide.image_selection.candidates || [],
                selected_url:
                    slide.image_selection.selected_url || null
              }
              : null
        })
    );

    const outline: OutlineResponse = {
      title: this.title.trim() || 'Presentation',

      subtitle: this.subtitle.trim(),

      presenters: this.presenters
          .map(p => p.trim())
          .filter(Boolean),

      date: this.date?.trim() || null,

      palettes: [...this.palettes],
      palette: { ...this.palette },
      selected_palette_index: this.selectedPaletteIndex,

      slides
    };

    this.state.setOutline(outline);

    const request: ConfirmOutlineRequest = {
      title: outline.title,

      subtitle: outline.subtitle,

      presenters: outline.presenters,
      date: outline.date,

      tone: this.state.tone(),

      palette: { ...this.palette },

      slides
    };

    this.api.generateHtml(request).subscribe({

      next: (presentation: Presentation) => {
        this.state.setPresentation(presentation);

        this.state.goTo(3);

        this.loading = false;

        this.progress = '';
      },

      error: (err) => {
        console.error('HTML generation failed:', err);

        this.error =
            err?.error?.detail ||
            err?.error?.message ||
            err?.message ||
            'HTML generation failed';

        this.loading = false;

        this.progress = '';
      }

    });
  }

  addStat(slide: SlideContent) {
    if (!slide.stats) {
      slide.stats = [];
    }

    slide.stats.push({
      value: '',
      label: '',
      context: ''
    });

    this.saveChanges();
  }

  removeStat(
      slide: SlideContent,
      index: number
  ) {
    slide.stats.splice(index, 1);
    this.saveChanges();
  }

  addTimelineItem(slide: SlideContent) {
    if (!slide.timeline) {
      slide.timeline = [];
    }

    slide.timeline.push({
      period: '',
      title: '',
      description: ''
    });

    this.saveChanges();
  }

  removeTimelineItem(
      slide: SlideContent,
      index: number
  ) {
    slide.timeline.splice(index, 1);
    this.saveChanges();
  }

  addChart(slide: SlideContent) {
    slide.chart = {
      title: '',
      type: 'bar',
      description: '',
      data: []
    };

    this.saveChanges();
  }

  removeChart(slide: SlideContent) {
    slide.chart = null;
    this.saveChanges();
  }

  private normalizeChartDataRows(
      slide: SlideContent
  ): any[] {

    if (!slide.chart) {
      return [];
    }

    if (!Array.isArray(slide.chart.data)) {
      slide.chart.data = [];
      return slide.chart.data;
    }

    slide.chart.data = slide.chart.data.map(
        (item: any) => {

          if (item && typeof item === 'object') {
            return {
              label: item.label ?? '',
              value: item.value ?? ''
            };
          }

          return {
            label: '',
            value: item ?? ''
          };
        }
    );

    return slide.chart.data;
  }

  getChartDataRows(
      slide: SlideContent
  ): any[] {
    return this.normalizeChartDataRows(slide);
  }

  addChartDataRow(
      slide: SlideContent
  ) {
    const rows = this.normalizeChartDataRows(slide);

    rows.push({
      label: '',
      value: ''
    });

    this.saveChanges();
  }

  removeChartDataRow(
      slide: SlideContent,
      index: number
  ) {
    const rows = this.normalizeChartDataRows(slide);

    rows.splice(index, 1);

    this.saveChanges();
  }
}