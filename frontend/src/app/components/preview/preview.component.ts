import {
  Component,
  inject,
  OnInit,
  AfterViewChecked,
  ElementRef,
  ViewChild,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { StateService } from '../../services/state.service';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import {Button} from "primeng/button";
import {InputText} from "primeng/inputtext";

@Component({
  selector: 'app-preview',
  standalone: true,
  imports: [CommonModule, FormsModule, Button, InputText],
  templateUrl: './preview.component.html',
  styleUrl: './preview.component.css',
})
export class PreviewComponent implements OnInit, AfterViewChecked {
  private api = inject(ApiService);
  state = inject(StateService);
  private sanitizer = inject(DomSanitizer);

  @ViewChild('slideFrame') slideFrame!: ElementRef<HTMLDivElement>;

  regenInstruction = '';
  regenerating = false;
  exporting = false;
  error = '';
  scale = 1;
  private needsScale = true;

  ngOnInit() {
    if (!this.state.presentation()) {
      this.state.goTo(1);
    }
  }

  ngAfterViewChecked() {
    if (this.needsScale) {
      this.needsScale = false;
      this.updateScale();
    }
  }

  get presentation() {
    return this.state.presentation();
  }

  get currentIndex() {
    return this.state.currentSlideIndex();
  }

  get currentSlide() {
    const p = this.presentation;
    if (!p?.slides?.length) return null;
    return p.slides[this.currentIndex];
  }

  safeHtml(html: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(html || '');
  }

  selectSlide(i: number) {
    this.state.currentSlideIndex.set(i);
    this.needsScale = true;
  }

  prev() {
    const i = this.currentIndex;
    if (i > 0) this.selectSlide(i - 1);
  }

  next() {
    const p = this.presentation;
    if (p && this.currentIndex < p.slides.length - 1) {
      this.selectSlide(this.currentIndex + 1);
    }
  }

  back() {
    this.state.goTo(2);
  }

  updateScale() {
    const frame = this.slideFrame?.nativeElement;
    if (!frame) return;
    const w = frame.clientWidth;
    this.scale = w / 1280;
    frame.style.height = `${720 * this.scale}px`;
  }

  regenerate() {
    const p = this.presentation;
    const slide = this.currentSlide;
    if (!p || !slide) return;

    this.regenerating = true;
    this.error = '';
    const instruction =
      this.regenInstruction.trim() ||
      'Improve the visual design while keeping the same content.';

    this.api
      .regenerateSlide({
        title: p.title,
        subtitle: p.subtitle || '',
        current_html: slide.html,
        instruction,
        tone: this.state.tone(),
        palette: p.palette,
      })
      .subscribe({
        next: (updated) => {
          const slides = [...p.slides];
          slides[this.currentIndex] = { ...slide, ...updated };
          this.state.setPresentation({ ...p, slides });
          this.state.currentSlideIndex.set(this.currentIndex);
          this.needsScale = true;
          this.regenerating = false;
        },
        error: (err) => {
          this.error = err?.error?.detail || err?.message || 'Regenerate failed';
          this.regenerating = false;
        },
      });
  }

  export(fmt: 'pptx' | 'html') {
    const p = this.presentation;
    if (!p) return;
    this.exporting = true;
    this.error = '';

    this.api.export(p, fmt).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const safe = (p.title || 'presentation').replace(/[^\w\-]+/g, '_').slice(0, 40);
        a.download = `${safe}.${fmt}`;
        a.click();
        URL.revokeObjectURL(url);
        this.exporting = false;
      },
      error: (err) => {
        this.error = err?.error?.detail || err?.message || 'Export failed';
        this.exporting = false;
      },
    });
  }
}
