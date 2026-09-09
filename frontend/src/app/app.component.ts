import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ApiService } from './services/api.service';
import {RouterOutlet} from "@angular/router";

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements OnInit {
  private api = inject(ApiService);

  healthLabel = 'Checking…';
  healthOk = false;

  ngOnInit() {
    this.api.health().subscribe({
      next: (h) => {
        console.log(h)
        this.healthLabel = `${h.provider} · ${h.azure_openai_5.used +' '+h.azure_openai_5.remaining || 'ok'}`;
        this.healthOk = true;
      },
      error: () => {
        this.healthLabel = 'Backend offline';
        this.healthOk = false;
      },
    });
  }
}
