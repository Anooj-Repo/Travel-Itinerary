import { Component, OnInit, AfterViewInit, ElementRef, ViewChild, HostListener } from '@angular/core';
import { GraphApiService } from './services/graph-api.service';
import * as d3 from 'd3';

interface ChatMessage {
  type: 'user' | 'assistant';
  text: string;
  reasoning?: string[];
  confidence?: number;
  justification?: string;
  timestamp: Date;
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type: string;
  isHighlighted?: boolean;
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string | GraphNode;
  target: string | GraphNode;
  relation: string;
  description?: string;
  isHighlighted?: boolean;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, AfterViewInit {
  @ViewChild('graphContainer', { static: false }) graphContainer!: ElementRef;

  // Source Manager Variables
  selectedFile: File | null = null;
  reliability = 1.0;
  uploadStatus = '';
  isUploading = false;
  documents: any[] = [];
  
  // Q&A Chat Variables
  queryText = '';
  isQuerying = false;
  chatHistory: ChatMessage[] = [];
  
  // Graph Data & State
  graphData: { nodes: GraphNode[]; links: GraphLink[] } = { nodes: [], links: [] };
  nodeTypes: string[] = ['Person', 'Place', 'Organization', 'Technology', 'Event', 'Concept'];
  selectedNode: any = null;

  // D3 Visualization variables
  private svg: any;
  private simulation: any;
  private width = 800;
  private height = 550;
  private zoomBehavior: any;

  constructor(private apiService: GraphApiService) {}

  ngOnInit() {
    this.loadDocuments();
    this.loadGraphData();
    this.addWelcomeMessage();
  }

  ngAfterViewInit() {
    this.initSvg();
    this.updateGraphVisualization();
  }

  @HostListener('window:resize')
  onResize() {
    this.resizeGraph();
  }

  private addWelcomeMessage() {
    this.chatHistory.push({
      type: 'assistant',
      text: 'Hello! I am your Knowledge Graph reasoning companion. Please upload text documents or PDF specifications. Once processed, you can ask me multi-hop questions (e.g. tracing relationships between people, concepts, and locations) and I will show you the reasoning path on the canvas!',
      timestamp: new Date()
    });
  }

  // 1. Source Manager Actions
  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.selectedFile = file;
      this.uploadStatus = `Selected: ${file.name}`;
    }
  }

  uploadDocument() {
    if (!this.selectedFile) return;

    this.isUploading = true;
    this.uploadStatus = 'Extracting entities & relations using GPT-4o...';

    this.apiService.uploadDocument(this.selectedFile, this.reliability).subscribe({
      next: (res) => {
        this.isUploading = false;
        this.selectedFile = null;
        this.uploadStatus = res.message;
        this.loadDocuments();
        this.loadGraphData();
      },
      error: (err) => {
        this.isUploading = false;
        this.uploadStatus = `Error: ${err.error?.error || 'Failed to parse file.'}`;
        console.error(err);
      }
    });
  }

  loadDocuments() {
    this.apiService.getUploadedDocuments().subscribe({
      next: (res) => {
        this.documents = res.documents || [];
      },
      error: (err) => console.error('Error loading documents:', err)
    });
  }

  clearGraph() {
    if (confirm('Are you sure you want to completely wipe the Knowledge Graph? This cannot be undone.')) {
      this.apiService.clearGraph().subscribe({
        next: (res) => {
          this.uploadStatus = 'Graph cleared successfully.';
          this.documents = [];
          this.graphData = { nodes: [], links: [] };
          this.chatHistory = [];
          this.addWelcomeMessage();
          this.updateGraphVisualization();
        },
        error: (err) => console.error('Error clearing graph:', err)
      });
    }
  }

  // 2. Q&A Query Actions
  submitQuery() {
    if (!this.queryText.trim() || this.isQuerying) return;

    const userQuery = this.queryText;
    this.chatHistory.push({
      type: 'user',
      text: userQuery,
      timestamp: new Date()
    });
    
    this.queryText = '';
    this.isQuerying = true;

    this.apiService.queryGraph(userQuery).subscribe({
      next: (res) => {
        this.isQuerying = false;
        this.chatHistory.push({
          type: 'assistant',
          text: res.answer,
          reasoning: res.reasoning_path,
          confidence: res.confidence_score,
          justification: res.confidence_justification,
          timestamp: new Date()
        });
        
        // Update the graph visualization with the highlighted reasoning path
        if (res.subgraph) {
          this.graphData = res.subgraph;
          this.updateGraphVisualization();
        }
      },
      error: (err) => {
        this.isQuerying = false;
        this.chatHistory.push({
          type: 'assistant',
          text: `An error occurred: ${err.error?.error || 'Failed to process query.'}`,
          timestamp: new Date()
        });
        console.error(err);
      }
    });
  }

  loadGraphData() {
    this.apiService.getGraphData().subscribe({
      next: (res) => {
        if (res.graph) {
          this.graphData = res.graph;
          this.updateGraphVisualization();
        }
      },
      error: (err) => console.error('Error loading graph data:', err)
    });
  }

  // 3. D3 SVG Graph Initialization & Force Layout
  private initSvg() {
    if (!this.graphContainer) return;
    
    const container = this.graphContainer.nativeElement;
    this.width = container.clientWidth || 800;
    this.height = container.clientHeight || 550;

    // Create SVG element
    this.svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', `0 0 ${this.width} ${this.height}`)
      .attr('style', 'background-color: #0b0f19; border-radius: 12px;');

    // Add arrow markers for links
    const defs = this.svg.append('defs');
    
    // Normal link marker
    defs.append('marker')
      .attr('id', 'arrow-normal')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22) // Place arrow head at edge of node
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', 'rgba(255, 255, 255, 0.25)');

    // Highlighted link marker
    defs.append('marker')
      .attr('id', 'arrow-highlighted')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#f59e0b'); // Golden yellow arrow

    // Add zoom container group
    const g = this.svg.append('g').attr('class', 'graph-group');

    // Setup zoom/pan behavior
    this.zoomBehavior = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    this.svg.call(this.zoomBehavior);
  }

  private resizeGraph() {
    if (!this.graphContainer || !this.svg) return;
    const container = this.graphContainer.nativeElement;
    this.width = container.clientWidth;
    this.height = container.clientHeight;
    this.svg.attr('viewBox', `0 0 ${this.width} ${this.height}`);
    if (this.simulation) {
      this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2)).alpha(0.3).restart();
    }
  }

  private updateGraphVisualization() {
    if (!this.svg) return;

    const g = this.svg.select('.graph-group');
    g.selectAll('*').remove(); // Clear previous rendering

    const nodes: GraphNode[] = JSON.parse(JSON.stringify(this.graphData.nodes));
    const links: GraphLink[] = JSON.parse(JSON.stringify(this.graphData.links));

    if (nodes.length === 0) {
      g.append('text')
        .attr('x', this.width / 2)
        .attr('y', this.height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#64748b')
        .attr('font-size', '16px')
        .text('Knowledge Graph visualization will appear here after uploading sources.');
      return;
    }

    // Color mapper for node categories
    const colorMap: { [key: string]: string } = {
      'person': '#6366f1',       // Indigo
      'place': '#10b981',        // Emerald green
      'organization': '#3b82f6', // Ocean blue
      'technology': '#ec4899',   // Hot pink
      'event': '#f59e0b',        // Amber gold
      'concept': '#8b5cf6'       // Purple
    };

    const getNodeColor = (type: string) => {
      const t = type.toLowerCase();
      return colorMap[t] || '#64748b'; // Slate gray default
    };

    // Initialize Simulation
    this.simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(35));

    // Render Edges/Links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', (d: any) => d.isHighlighted ? '#f59e0b' : 'rgba(255, 255, 255, 0.12)')
      .attr('stroke-width', (d: any) => d.isHighlighted ? 3 : 1.2)
      .attr('marker-end', (d: any) => d.isHighlighted ? 'url(#arrow-highlighted)' : 'url(#arrow-normal)');

    // Render Edge Labels (Relations)
    const linkText = g.append('g')
      .attr('class', 'link-labels')
      .selectAll('text')
      .data(links)
      .enter()
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('font-size', '9px')
      .attr('fill', (d: any) => d.isHighlighted ? '#fbbf24' : '#64748b')
      .attr('font-weight', (d: any) => d.isHighlighted ? '600' : '400')
      .text((d: any) => d.relation);

    // Render Nodes (Groups)
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node-group')
      .call(d3.drag()
        .on('start', (event: any, d: any) => {
          if (!event.active) this.simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event: any, d: any) => {
          if (!event.active) this.simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      )
      .on('click', (event: any, d: any) => {
        this.selectedNode = d;
      });

    // Render Node Circles
    node.append('circle')
      .attr('r', (d: any) => d.isHighlighted ? 15 : 12)
      .attr('fill', (d: any) => getNodeColor(d.type))
      .attr('stroke', (d: any) => d.isHighlighted ? '#fbbf24' : '#0b0f19')
      .attr('stroke-width', (d: any) => d.isHighlighted ? 3.5 : 1.5)
      .attr('style', (d: any) => d.isHighlighted ? 'filter: drop-shadow(0 0 8px #fbbf24); cursor: pointer;' : 'cursor: pointer;');

    // Render Node Labels (Text)
    node.append('text')
      .attr('dy', 25)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '11px')
      .attr('font-weight', (d: any) => d.isHighlighted ? '700' : '500')
      .text((d: any) => d.label);

    // Render Node Type Indicator Tooltips (small hover flag)
    node.append('title')
      .text((d: any) => `${d.label} [${d.type}]`);

    // Bind simulation update callback
    this.simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      linkText
        .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
        .attr('y', (d: any) => (d.source.y + d.target.y) / 2 - 5);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Reset zoom to fit nodes smoothly
    this.zoomToFit(nodes);
  }

  private zoomToFit(nodes: GraphNode[]) {
    if (nodes.length === 0 || !this.svg || !this.zoomBehavior) return;

    // Calculate bounding box of nodes
    let minX = d3.min(nodes, (d: any) => d.x) || 0;
    let maxX = d3.max(nodes, (d: any) => d.x) || 0;
    let minY = d3.min(nodes, (d: any) => d.y) || 0;
    let maxY = d3.max(nodes, (d: any) => d.y) || 0;

    const dx = maxX - minX;
    const dy = maxY - minY;
    const cx = (minX + maxX) / 2;
    const cy = (minY + maxY) / 2;

    const scale = Math.min(0.9, 0.9 / Math.max(dx / this.width, dy / this.height));
    const translate = [this.width / 2 - scale * cx, this.height / 2 - scale * cy];

    this.svg.transition()
      .duration(750)
      .call(
        this.zoomBehavior.transform,
        d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
      );
  }

  resetZoom() {
    if (this.svg && this.zoomBehavior) {
      this.svg.transition()
        .duration(500)
        .call(this.zoomBehavior.transform, d3.zoomIdentity);
    }
  }
}
