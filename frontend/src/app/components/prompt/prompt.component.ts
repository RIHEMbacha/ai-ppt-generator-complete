import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TextareaModule } from 'primeng/textarea';
import { InputNumberModule } from 'primeng/inputnumber';
import { SelectModule } from 'primeng/select';
import { ApiService } from '../../services/api.service';
import { StateService } from '../../services/state.service';

@Component({
  selector: 'app-prompt',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TextareaModule,
    InputNumberModule,
    SelectModule
  ],
  templateUrl: './prompt.component.html',
  styleUrl: './prompt.component.css',
})
export class PromptComponent {
  private api = inject(ApiService);
  state = inject(StateService);

  @ViewChild('documentInput')
  documentInput?: ElementRef<HTMLInputElement>;

  prompt = '';
  numSlides = 8;
  tone = 'professional';

  loading = false;
  error = '';

  documentMode = false;
  selectedDocument: File | null = null;
  selectedDocumentName = '';

  tones = [
    { value: 'professional', label: 'Professional' },
    { value: 'bold', label: 'Bold & energetic' },
    { value: 'minimal', label: 'Minimal & clean' },
    { value: 'educational', label: 'Educational' },
    { value: 'startup', label: 'Startup pitch' },
    { value: 'funny', label: 'Funny' }
  ];

  toggleDocumentMode(): void {
    if (this.loading) {
      return;
    }

    this.documentMode = !this.documentMode;
    this.error = '';

    if (!this.documentMode) {
      this.removeDocument();
    }
  }

  openDocumentPicker(): void {
    if (this.loading) {
      return;
    }

    this.documentInput?.nativeElement.click();
  }

  onDocumentSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];

    if (!file) {
      return;
    }

    this.setDocument(file);

    input.value = '';
  }

  onDocumentDrop(event: DragEvent): void {
    event.preventDefault();

    if (this.loading) {
      return;
    }

    const file = event.dataTransfer?.files?.[0];

    if (!file) {
      return;
    }

    this.setDocument(file);
  }

  private setDocument(file: File): void {
    const allowedExtensions = [
      'pdf',
      'doc',
      'docx',
      'txt',
      'md'
    ];

    const extension = file.name
      .split('.')
      .pop()
      ?.toLowerCase();

    if (!extension || !allowedExtensions.includes(extension)) {
      this.error = 'Please select a PDF, DOC, DOCX, TXT or MD file.';
      return;
    }

    this.selectedDocument = file;
    this.selectedDocumentName = file.name;
    this.error = '';
  }

  removeDocument(event?: Event): void {
    event?.stopPropagation();

    this.selectedDocument = null;
    this.selectedDocumentName = '';

    if (this.documentInput?.nativeElement) {
      this.documentInput.nativeElement.value = '';
    }
  }

  generate(): void {
    this.error = '';

    if (this.documentMode) {
      this.generateFromDocument();
      return;
    }

    this.generateFromPrompt();
  }

  private generateFromPrompt(): void {
    if (!this.prompt.trim()) {
      this.error = 'Please enter a topic or brief.';
      return;
    }

    this.loading = true;
    this.state.tone.set(this.tone);

    this.api
      .generateOutline({
        prompt: this.prompt.trim(),
        num_slides: this.numSlides,
        tone: this.tone,
      })
      .subscribe({
        next: (outline) => {
          this.state.setOutline(outline);
          this.state.goTo(2);
          this.loading = false;
        },
        error: (err) => {
          this.error =
            err?.error?.detail ||
            err?.message ||
            'Outline generation failed';

          this.loading = false;
        },
      });
  }

  private generateFromDocument(): void {
    if (!this.selectedDocument) {
      this.error = 'Please select a document first.';
      return;
    }

    this.loading = true;
    this.state.tone.set(this.tone);

    this.api
      .generateOutlineFromDocument(
        this.selectedDocument,
        this.numSlides,
        this.tone
      )
      .subscribe({
        next: (outline) => {
          this.state.setOutline(outline);
          this.state.goTo(2);
          this.loading = false;
        },
        error: (err) => {
          this.error =
            err?.error?.detail ||
            err?.message ||
            'Document outline generation failed';

          this.loading = false;
        },
      });
  }
}
