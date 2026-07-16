import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class GraphApiService {
  private apiUrl = environment.apiUrl; // http://localhost:5005/api/graph

  constructor(private http: HttpClient) { }

  uploadDocument(file: File, reliability: number = 1.0): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('reliability', reliability.toString());
    return this.http.post(`${this.apiUrl}/upload`, formData);
  }

  queryGraph(query: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/query`, { query });
  }

  getGraphData(): Observable<any> {
    return this.http.get(`${this.apiUrl}/data`);
  }

  getUploadedDocuments(): Observable<any> {
    return this.http.get(`${this.apiUrl}/documents`);
  }

  clearGraph(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/clear`);
  }
}
