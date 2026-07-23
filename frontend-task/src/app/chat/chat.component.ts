import { Component, OnInit } from '@angular/core';
import { ChatService } from '../services/chat.service';
import { ChatMessage } from '../models/task-routing.model';

@Component({
  selector: 'app-chat',
  templateUrl: './chat.component.html',
  styleUrls: ['./chat.component.css']
})
export class ChatComponent implements OnInit {
  sessionId: string | null = null;
  messages: ChatMessage[] = [];
  userMessage: string = '';
  loading: boolean = false;
  error: string | null = null;

  // New Features: Image Upload, Voice Command, Speaker
  selectedImage: string | null = null;
  selectedFileName: string | null = null;
  isListening: boolean = false;
  isSpeaking: boolean = false;
  recognition: any = null;

  constructor(private chatService: ChatService) {}

  ngOnInit(): void {
    this.startNewSession();
  }

  startNewSession(): void {
    this.loading = true;
    this.chatService.startSession().subscribe({
      next: (response: any) => {
        this.sessionId = response.session_id;
        this.messages = [{
          role: 'assistant',
          content: 'Hello! I\'m your AI assistant for task routing. I can help you understand routing decisions, explore alternatives, and answer questions about resource assignments. How can I help you today?',
          timestamp: new Date()
        }];
        this.loading = false;
      },
      error: (err: any) => {
        this.error = 'Failed to start chat session. Please try again.';
        this.loading = false;
        console.error('Chat session error:', err);
      }
    });
  }

  // File / Image Upload Handler
  onFileSelected(event: any): void {
    const file: File = event.target.files?.[0];
    if (file) {
      if (!file.type.startsWith('image/')) {
        alert('Please select a valid image file.');
        return;
      }
      this.selectedFileName = file.name;
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.selectedImage = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  }

  removeAttachment(): void {
    this.selectedImage = null;
    this.selectedFileName = null;
  }

  // Voice Command (Speech to Text)
  initSpeechRecognition(): void {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.lang = 'en-US';

      this.recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0])
          .map((result: any) => result.transcript)
          .join('');
        this.userMessage = transcript;
      };

      this.recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        this.isListening = false;
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };
    }
  }

  toggleVoiceCommand(): void {
    if (!this.recognition) {
      this.initSpeechRecognition();
    }
    if (!this.recognition) {
      alert('Speech Recognition is not supported by your browser. Please use Google Chrome or Microsoft Edge.');
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
      this.isListening = false;
    } else {
      this.isListening = true;
      this.recognition.start();
    }
  }

  // Text-to-Speech / Speaker Handler
  speakText(text: string): void {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-Speech is not supported by your browser.');
      return;
    }

    window.speechSynthesis.cancel();

    if (!text) return;

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      this.isSpeaking = true;
    };
    utterance.onend = () => {
      this.isSpeaking = false;
    };
    utterance.onerror = () => {
      this.isSpeaking = false;
    };

    window.speechSynthesis.speak(utterance);
  }

  toggleSpeaker(): void {
    if (this.isSpeaking) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
    } else {
      const lastAssistantMsg = [...this.messages].reverse().find(m => m.role === 'assistant');
      if (lastAssistantMsg) {
        this.speakText(lastAssistantMsg.content);
      }
    }
  }

  sendMessage(): void {
    if ((!this.userMessage.trim() && !this.selectedImage) || !this.sessionId) {
      return;
    }

    const userText = this.userMessage.trim();
    const userMsg: ChatMessage = {
      role: 'user',
      content: userText || (this.selectedFileName ? `Attached image: ${this.selectedFileName}` : 'Uploaded image'),
      timestamp: new Date(),
      image: this.selectedImage || undefined
    };
    
    this.messages.push(userMsg);

    const messageToSend = userText || 'Analyzed uploaded image content for task routing.';
    
    // Clear input state
    this.userMessage = '';
    this.selectedImage = null;
    this.selectedFileName = null;
    this.loading = true;

    if (this.isListening && this.recognition) {
      this.recognition.stop();
      this.isListening = false;
    }

    this.chatService.sendMessage(this.sessionId, messageToSend).subscribe({
      next: (response: any) => {
        const assistantMsg: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date()
        };
        this.messages.push(assistantMsg);
        this.loading = false;
        this.scrollToBottom();
      },
      error: (err: any) => {
        this.error = 'Failed to send message. Please try again.';
        this.loading = false;
        console.error('Chat message error:', err);
      }
    });
  }

  clearChat(): void {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      this.isSpeaking = false;
    }
    if (this.sessionId) {
      this.chatService.clearSession(this.sessionId).subscribe();
    }
    this.startNewSession();
  }

  scrollToBottom(): void {
    setTimeout(() => {
      const chatContainer = document.querySelector('.messages-container');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 100);
  }

  onKeyPress(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
