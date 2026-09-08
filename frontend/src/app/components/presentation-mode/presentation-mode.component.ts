import {
  Component,
  HostListener,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { Router } from '@angular/router';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-presentation-mode',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './presentation-mode.component.html',
  styleUrl: './presentation-mode.component.css',
})
export class PresentationModeComponent implements OnInit, OnDestroy {
  state = inject(StateService);
  private sanitizer = inject(DomSanitizer);
  private router = inject(Router);

  private notesWindow: Window | null = null;
  private controlsTimer: ReturnType<typeof setTimeout> | null = null;

  showControls = false;

  get presentation() {
    return this.state.presentation();
  }

  get currentIndex() {
    return this.state.currentSlideIndex();
  }

  get currentSlide() {
    const p = this.presentation;

    if (!p?.slides?.length) {
      return null;
    }

    return p.slides[this.currentIndex];
  }

  ngOnInit() {
    if (!this.presentation) {
      this.router.navigate(['/']);
      return;
    }

    document.body.classList.add('presentation-active');

    setTimeout(() => {
      this.requestFullscreen();
    });
  }

  ngOnDestroy() {
    document.body.classList.remove('presentation-active');

    if (this.controlsTimer) {
      clearTimeout(this.controlsTimer);
    }

    this.closeNotesWindow();

    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {});
    }
  }

  safeHtml(html: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(html || '');
  }

  next() {
    const p = this.presentation;

    if (!p) return;

    if (this.currentIndex < p.slides.length - 1) {
      this.state.currentSlideIndex.set(this.currentIndex + 1);
      this.syncNotesWindow();
      this.showControlsTemporarily();
    }
  }

  previous() {
    if (this.currentIndex > 0) {
      this.state.currentSlideIndex.set(this.currentIndex - 1);
      this.syncNotesWindow();
      this.showControlsTemporarily();
    }
  }

  exitPresentation() {
  this.state.goTo(3)
  }

  openPresenterNotes() {
    if (this.notesWindow && !this.notesWindow.closed) {
      this.notesWindow.focus();
      return;
    }

    const width = 500;
    const height = 700;

    this.notesWindow = window.open(
        '',
        'presentation-presenter-notes',
        `width=${width},height=${height}`
    );

    if (!this.notesWindow) {
      return;
    }

    this.renderNotesWindow();

    this.notesWindow.onbeforeunload = () => {
      this.notesWindow = null;
    };

    this.showControlsTemporarily();
  }

  private renderNotesWindow() {
    if (!this.notesWindow) return;

    const slide = this.currentSlide;
    const p = this.presentation;

    if (!slide || !p) return;

    const nextSlide = p.slides[this.currentIndex + 1];

    this.notesWindow.document.open();

    this.notesWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Presenter Notes</title>

        <style>
          * {
            box-sizing: border-box;
          }

          body {
            margin: 0;
            padding: 28px;
            background: #0f172a;
            color: #f8fafc;
            font-family:
              Inter,
              system-ui,
              -apple-system,
              BlinkMacSystemFont,
              "Segoe UI",
              sans-serif;
          }

          .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
          }

          .eyebrow {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: #94a3b8;
          }

          .counter {
            font-size: 14px;
            color: #94a3b8;
          }

          .title {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 24px;
          }

          .notes {
            padding: 22px;
            border-radius: 18px;
            background: rgba(255,255,255,.08);
            border: 1px solid rgba(255,255,255,.12);
            line-height: 1.7;
            font-size: 16px;
          }

          .next {
            margin-top: 24px;
            padding: 18px;
            border-radius: 16px;
            background: rgba(255,255,255,.05);
          }

          .next-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #94a3b8;
            margin-bottom: 8px;
          }

          .next-title {
            font-size: 16px;
            font-weight: 600;
          }
        </style>
      </head>

      <body>

        <div class="header">
          <div class="eyebrow">
            PRESENTER
          </div>

          <div class="counter">
            ${this.currentIndex + 1} / ${p.slides.length}
          </div>
        </div>

        <div class="title">
          ${this.escapeHtml(
        slide.label || `Slide ${this.currentIndex + 1}`
    )}
        </div>

        <div class="notes">
          ${this.escapeHtml(
        slide.notes || 'No presenter notes for this slide.'
    )}
        </div>

        ${
        nextSlide
            ? `
              <div class="next">
                <div class="next-label">
                  Next slide
                </div>

                <div class="next-title">
                  ${this.escapeHtml(nextSlide.label || '')}
                </div>
              </div>
            `
            : ''
    }

      </body>
      </html>
    `);

    this.notesWindow.document.close();
  }

  private syncNotesWindow() {
    if (
        this.notesWindow &&
        !this.notesWindow.closed
    ) {
      this.renderNotesWindow();
    }
  }

  private closeNotesWindow() {
    if (
        this.notesWindow &&
        !this.notesWindow.closed
    ) {
      this.notesWindow.close();
    }

    this.notesWindow = null;
  }

  private requestFullscreen() {
    document.documentElement
        .requestFullscreen?.()
        .catch(() => {});
  }

  private showControlsTemporarily() {
    this.showControls = true;

    if (this.controlsTimer) {
      clearTimeout(this.controlsTimer);
    }

    this.controlsTimer = setTimeout(() => {
      this.showControls = false;
    }, 1000);
  }

  private hideControls() {
    if (this.controlsTimer) {
      clearTimeout(this.controlsTimer);
    }

    this.showControls = false;
  }

  private escapeHtml(value: string): string {
    return value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
  }

  @HostListener('document:mousemove')
  handleMouseMove() {
    this.showControlsTemporarily();
  }

  @HostListener('document:keydown', ['$event'])
  handleKeyboard(event: KeyboardEvent) {
    switch (event.key) {
      case 'ArrowRight':
      case 'PageDown':
      case ' ':
        event.preventDefault();
        this.next();
        break;

      case 'ArrowLeft':
      case 'PageUp':
        event.preventDefault();
        this.previous();
        break;

      case 'Escape':
        this.exitPresentation();
        break;
    }
  }
}