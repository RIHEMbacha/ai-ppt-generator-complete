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
   error: string='';

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

  }

  ngOnDestroy() {
    document.body.classList.remove('presentation-active');

    if (this.controlsTimer) {
      clearTimeout(this.controlsTimer);
    }

    this.closeNotesWindow();

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

  async openPresenterNotes() {
    const documentPiP = (window as any).documentPictureInPicture;

    if (!documentPiP) {
      this.error = 'Document Picture-in-Picture is not supported in this browser.';
      return;
    }

    if (documentPiP.window) {
      documentPiP.window.focus();
      return;
    }

    try {
      const pipWindow = await documentPiP.requestWindow({
        width: 460,
        height: 650,
      });

      this.notesWindow = pipWindow;

      this.renderNotesWindow();

      pipWindow.addEventListener('pagehide', () => {
        this.notesWindow = null;
      });
    } catch (error) {
      console.error('Failed to open presenter notes:', error);
    }
  }

  renderNotesWindow() {
    if (!this.notesWindow) return;

    const slide = this.currentSlide;
    const p = this.presentation;

    if (!slide || !p) return;

    const nextSlide = p.slides[this.currentIndex + 1];

    const doc = this.notesWindow.document;

    doc.head.innerHTML = `
        <title>Presenter Notes</title>

        <style>
            * {
                box-sizing: border-box;
            }

            html,
            body {
                margin: 0;
                width: 100%;
                height: 100%;
            }

            body {
                padding: 24px;
                background:
                    radial-gradient(
                        circle at top right,
                        rgba(99, 102, 241, 0.22),
                        transparent 40%
                    ),
                    #0f172a;
                color: #f8fafc;
                font-family:
                    Inter,
                    system-ui,
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    sans-serif;
                overflow: auto;
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
                font-size: 13px;
                color: #94a3b8;
                font-weight: 600;
            }

            .title {
                font-size: 22px;
                line-height: 1.3;
                font-weight: 700;
                margin-bottom: 20px;
            }

            .notes {
                padding: 20px;
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                line-height: 1.7;
                font-size: 15px;
                color: #e2e8f0;
            }

            .next {
                margin-top: 20px;
                padding: 18px;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
            }

            .next-label {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #94a3b8;
                margin-bottom: 8px;
                font-weight: 700;
            }

            .next-title {
                font-size: 15px;
                font-weight: 600;
                color: #f8fafc;
            }

            .progress {
                position: fixed;
                left: 0;
                bottom: 0;
                height: 3px;
                background: #6366f1;
                width: ${((this.currentIndex + 1) / p.slides.length) * 100}%;
            }
        </style>
    `;

    doc.body.innerHTML = `
        <div class="header">
            <div class="eyebrow">PRESENTER</div>

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
                            ${this.escapeHtml(
                nextSlide.label ||
                `Slide ${this.currentIndex + 2}`
            )}
                        </div>
                    </div>
                `
            : ''
    }

        <div class="progress"></div>
    `;
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


  private showControlsTemporarily() {
    this.showControls = true;

    if (this.controlsTimer) {
      clearTimeout(this.controlsTimer);
    }

    this.controlsTimer = setTimeout(() => {
      this.showControls = false;
    }, 1000);
  }

   hideControls() {
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