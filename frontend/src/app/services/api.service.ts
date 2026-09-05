import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  OutlineResponse,
  Presentation,
  Slide,
  GenerateOutlineRequest,
  ConfirmOutlineRequest,
  RegenerateSlideRequest,
} from '../models/presentation.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  health(): Observable<{ status: string; provider: string; model: string }> {
    return this.http.get<{ status: string; provider: string; model: string }>(
      `${this.base}/api/health`
    );
  }

  /** Phase 1 – content plan only */
  generateOutline(req: GenerateOutlineRequest): Observable<OutlineResponse> {
    return this.http.post<OutlineResponse>(`${this.base}/api/outline`, req);
  }

  generateOutlineFromDocument(file: File, numSlides: number, tone: string): Observable<OutlineResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('num_slides', String(numSlides));
    formData.append('tone', tone);
    return this.http.post<OutlineResponse>(`${this.base}/api/outline/document`, formData);
  }

  /** Phase 2 – HTML for every slide (independent prompts) */
  generateHtml(req: ConfirmOutlineRequest): Observable<Presentation> {
    return this.http.post<Presentation>(`${this.base}/api/generate-html`, req);
  }

  regenerateSlide(req: RegenerateSlideRequest): Observable<Slide> {
    return this.http.post<Slide>(`${this.base}/api/regenerate-slide`, req);
  }

  export(presentation: Presentation, format: 'pptx' | 'pdf' | 'html' = 'pptx'): Observable<Blob> {
    return this.http.post(
      `${this.base}/api/export`,
      { presentation, format },
      { responseType: 'blob' }
    );
  }
}
