import { Component, inject } from '@angular/core';
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
  imports: [CommonModule, FormsModule, TextareaModule, InputNumberModule, SelectModule],
  templateUrl: './prompt.component.html',
  styleUrl: './prompt.component.css',
})
export class PromptComponent {
  private api = inject(ApiService);
  state = inject(StateService);

  prompt = '';
  numSlides = 8;
  tone = 'professional';
  loading = false;
  error = '';

  tones = [
    { value: 'professional', label: 'Professional' },
    { value: 'bold', label: 'Bold & energetic' },
    { value: 'minimal', label: 'Minimal & clean' },
    { value: 'educational', label: 'Educational' },
    { value: 'startup', label: 'Startup pitch' },
    { value: 'funny', label: 'Funny' },

  ];

  generate() {
    if (!this.prompt.trim()) {
      this.error = 'Please enter a topic or brief.';
      return;
    }
    this.error = '';
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
          this.error = err?.error?.detail || err?.message || 'Outline generation failed';
          this.loading = false;
        },
      });
  }
}
