import { Injectable, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { OutlineResponse, Presentation } from '../models/presentation.models';

@Injectable({
  providedIn: 'root'
})
export class StateService {
  private router = inject(Router);

  private readonly STORAGE_KEY = 'slideforge_state';

  step = signal<1 | 2 | 3>(1);
  tone = signal('professional');
  outline = signal<OutlineResponse | null>(null);
  presentation = signal<Presentation | null>(null);
  currentSlideIndex = signal(0);

  constructor() {
    this.restore();
  }

  goTo(step: 1 | 2 | 3) {
    this.step.set(step);
    this.save();

    const routes: Record<1 | 2 | 3, string> = {
      1: '/prompt',
      2: '/outline',
      3: '/preview'
    };

    void this.router.navigateByUrl(routes[step]);
  }

  setOutline(outline: OutlineResponse) {
    this.outline.set(outline);
    this.save();
  }

  setPresentation(presentation: Presentation) {
    this.presentation.set(presentation);
    this.currentSlideIndex.set(0);
    this.save();
  }

  setCurrentSlideIndex(index: number) {
    this.currentSlideIndex.set(index);
    this.save();
  }

  updateOutline(outline: OutlineResponse) {
    this.outline.set(outline);
    this.save();
  }

  save() {
    const data = {
      step: this.step(),
      tone: this.tone(),
      outline: this.outline(),
      presentation: this.presentation(),
      currentSlideIndex: this.currentSlideIndex()
    };

    localStorage.setItem(
        this.STORAGE_KEY,
        JSON.stringify(data)
    );
  }

  restore() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);

      if (!stored) {
        return;
      }

      const data = JSON.parse(stored);

      if (data.step === 1 || data.step === 2 || data.step === 3) {
        this.step.set(data.step);
      }

      if (data.tone) {
        this.tone.set(data.tone);
      }

      if (data.outline) {
        this.outline.set(data.outline);
      }

      if (data.presentation) {
        this.presentation.set(data.presentation);
      }

      if (typeof data.currentSlideIndex === 'number') {
        this.currentSlideIndex.set(data.currentSlideIndex);
      }
    } catch (error) {
      console.error('Failed to restore SlideForge state:', error);
      this.clearStorage();
    }
  }

  reset() {
    this.step.set(1);
    this.tone.set('professional');
    this.outline.set(null);
    this.presentation.set(null);
    this.currentSlideIndex.set(0);

    this.clearStorage();

    void this.router.navigateByUrl('/prompt');
  }

  clearStorage() {
    localStorage.removeItem(this.STORAGE_KEY);
  }
}