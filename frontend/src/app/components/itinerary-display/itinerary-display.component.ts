// import { Component, Input, Output, EventEmitter } from '@angular/core';
// import { TripItinerary } from '../../models/itinerary.model';

// @Component({
//   selector: 'app-itinerary-display',
//   templateUrl: './itinerary-display.component.html',
//   styleUrls: ['./itinerary-display.component.scss']
// })
// export class ItineraryDisplayComponent {
//   @Input() itinerary?: TripItinerary;
//   @Output() exportRequest = new EventEmitter<string>();

//   exportItinerary(format: string) {
//     this.exportRequest.emit(format);
//   }

//   printItinerary() {
//     window.print();
//   }
// }

import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnChanges,
  SimpleChanges
} from '@angular/core';

import { TripItinerary } from '../../models/itinerary.model';

interface ParsedSection {
  period: string;
  activities: string[];
}

interface ParsedDay {
  dayNumber: number;
  date: string;
  sections: ParsedSection[];
}

@Component({
  selector: 'app-itinerary-display',
  templateUrl: './itinerary-display.component.html',
  styleUrls: ['./itinerary-display.component.scss']
})
export class ItineraryDisplayComponent implements OnChanges {

  @Input() itinerary?: TripItinerary;

  @Output()
  exportRequest = new EventEmitter<string>();

  parsedDays: ParsedDay[] = [];

  ngOnChanges(): void {

    const raw =
      this.itinerary?.raw_itinerary ||
      (this.itinerary as any)?.itinerary?.raw_itinerary ||
      (this.itinerary as any)?.itinerary?.itinerary?.raw_itinerary;

    console.log('RAW ITINERARY:', raw);

    if (raw) {
      this.parsedDays = this.parseRawItinerary(raw);
    } else {
      this.parsedDays = [];
    }

    console.log('PARSED DAYS:', this.parsedDays);
  }

  exportItinerary(format: string) {
    this.exportRequest.emit(format);
  }

  printItinerary() {
    window.print();
  }

  private parseRawItinerary(raw: string): ParsedDay[] {

  try {

    // 1. Extract JSON block from mixed text
    const jsonStart = raw.indexOf('{');
    const jsonEnd = raw.lastIndexOf('}') + 1;

    const jsonString = raw.substring(jsonStart, jsonEnd);

    const parsed = JSON.parse(jsonString);

    // 2. Convert LLM JSON → UI format
    const days = parsed.days || [];

    return days.map((d: any, index: number) => {

      const sections: ParsedSection[] = [];

      if (d.morning?.length) {
        sections.push({
          period: 'Morning',
          activities: d.morning.map((a: any) => a.activity)
        });
      }

      if (d.afternoon?.length) {
        sections.push({
          period: 'Afternoon',
          activities: d.afternoon.map((a: any) => a.activity)
        });
      }

      if (d.evening?.length) {
        sections.push({
          period: 'Evening',
          activities: d.evening.map((a: any) => a.activity)
        });
      }

      return {
        dayNumber: index + 1,
        date: d.date,
        sections
      };

    });

  } catch (e) {
    console.error('Parse error:', e);
    return [];
  }
}

  private processActivityLine(
    line: string,
    currentDay: ParsedDay,
    sectionRegex: RegExp
  ) {

    // Detect inline section
    const match = line.match(/^(Morning|Afternoon|Evening|Night)\s*:?\s*(.*)$/i);

    let period = 'General';
    let activityText = line;

    if (match) {
      period = match[1];
      activityText = match[2]?.trim() || '';
    }

    let section = currentDay.sections.find(
      s => s.period === period
    );

    if (!section) {
      section = {
        period,
        activities: []
      };
      currentDay.sections.push(section);
    }

    if (activityText) {
      section.activities.push(activityText);
    }
  }

}