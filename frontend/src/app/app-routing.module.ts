import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { PromptComponent } from './components/prompt/prompt.component';
import { OutlineComponent } from './components/outline/outline.component';
import { PreviewComponent } from './components/preview/preview.component';
import {PresentationModeComponent} from "./components/presentation-mode/presentation-mode.component";

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'prompt',
  },
  {
    path: 'prompt',
    component: PromptComponent,
    title: 'SlideForge AI — Create',
  },
  {
    path: 'outline',
    component: OutlineComponent,
    title: 'SlideForge AI — Review outline',
  },
  {
    path: 'preview',
    component: PreviewComponent,
    title: 'SlideForge AI — Preview',
  },
  {
    path: 'presentation',
    component: PresentationModeComponent
  },
  {
    path: '**',
    redirectTo: 'prompt',
  },
];

@NgModule({
  imports: [RouterModule.forRoot(routes, {
    bindToComponentInputs: true,
    scrollPositionRestoration: 'top',
  })],
  exports: [RouterModule],
})
export class AppRoutingModule {}
