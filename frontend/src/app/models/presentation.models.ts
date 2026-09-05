
export interface ContentPoint {
  point: string;
  explanation?: string;
}

export interface Stat {
  value: string;
  label: string;
  context?: string;
}

export interface Chart {
  type?: string;
  title?: string;
  description?: string;
  data?: any[];
  [key: string]: any;
}

export interface TimelineItem {
  period: string;
  title: string;
  description: string;
}

export interface ImageCandidate {
  url: string;
  thumbnail_url?: string;
  width: number;
  height: number;
  file_size: number;
  photographer: string;
  score: number;
}

export interface ImageSelection {
  query: string;
  candidates: ImageCandidate[];
  selected_url: string | null;
}

export interface SlideContent {
  label: string;
  notes: string;
  objective: string;

  points: ContentPoint[];

  stats: Stat[];

  chart: Chart | null;

  timeline: TimelineItem[];

  layout_hint: string;

  image_query: string;

  image_selection: ImageSelection | null;
}
export interface Slide {
  label: string;
  notes: string;
  content?: string;
  layout_hint?: string;
  html: string;
}

export interface Palette {
  name: string;
  bg: string;
  surface: string;
  primary: string;
  accent: string;
  text: string;
  muted: string;
}

export interface OutlineResponse {
  title: string;
  subtitle: string;
  presenters: string[];
  date: string | null;
  palettes: Palette[];
  palette: Record<string, string>;
  selected_palette_index?: number;
  slides: SlideContent[];
}

export interface Presentation {
  title: string;
  subtitle: string;
  palette?: Record<string, string>;
  slides: Slide[];
}

export interface GenerateOutlineRequest {
  prompt: string;
  num_slides: number;
  tone: string;
}

export interface ConfirmOutlineRequest {
  title: string;
  subtitle: string;
  presenters: string[];
  date: string | null;
  tone: string;
  palette: Record<string, string>;
  slides: SlideContent[];
}

export interface RegenerateSlideRequest {
  title: string;
  subtitle: string;
  current_html: string;
  instruction: string;
  tone: string;
  palette?: Record<string, string>;
}

export const LAYOUT_HINTS = [
  'title',
  'agenda',
  'definition+pillars',
  'big-stats',
  'impact-list',
  'two-column',
  'cards-2x2',
  'numbered-takeaways',
  'chart-focus',
  'timeline',
  'closing',
  'content',
] as const;
