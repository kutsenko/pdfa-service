# User Story: Barrierefreie Kamera-Unterstützung für Blinde

**ID**: US-008
**Titel**: Audio-geführte Dokumentenerfassung mit automatischer Kantenerkennung
**Status**: ✅ Implementiert
**Datum**: 2026-01-01

---

## Story

**Als** blinder oder sehbehinderter Benutzer
**möchte ich** Dokumente mittels Audio-Führung fotografieren können
**damit** ich ohne visuelle Kontrolle hochwertige Dokumentenscans erstellen kann, die automatisch zugeschnitten und perspektivkorrigiert werden.

---

## Kontext

**Aktueller Zustand (vor Accessibility Feature)**:
- Kamera-Interface nur visuell bedienbar
- Keine Audio-Rückmeldung für Dokumentenposition
- Manuelles Zentrieren und Ausrichten erforderlich
- Keine Unterstützung für Screen Reader
- Blinde Benutzer können Service nicht nutzen

**Problem**:
- Barrierefreiheit ist gesetzlich vorgeschrieben (WCAG 2.1 Level AA)
- Blinde Benutzer können Dokumente nicht digitalisieren
- Keine Audio-Feedback für Kamera-Ausrichtung
- Manuelle Perspektivkorrektur für Sehbehinderte unmöglich

**Lösung**:
- Echtzeit-Kantenerkennung mit jscanify v1.4.0 und OpenCV.js 4.7.0
- Audio-Feedback via Web Audio API (Töne) und Speech Synthesis API (Sprachansagen)
- Automatische Auslösung bei stabiler Dokumentenerkennung
- Automatischer Zuschnitt und Perspektivkorrektur
- iOS Safari Kompatibilität (spezielle Behandlung)
- Mehrsprachig (de, en, es, fr)

---

## Akzeptanzkriterien

### 1. Screen Reader Auto-Detection
- **Given** ein Benutzer öffnet die Kamera-Seite
- **When** ein Screen Reader aktiv ist (z.B. VoiceOver, NVDA, JAWS)
- **Then** sollte die Accessibility-Assistance automatisch aktiviert werden
- **And** sollte eine Sprachansage "Camera assistance enabled" erfolgen

### 2. Audio-Unlock für iOS Safari
- **Given** ein Benutzer aktiviert Audio-Führung auf iOS Safari
- **When** der Checkbox angeklickt wird
- **Then** sollte AudioContext im User-Gesture erstellt und resumed werden
- **And** sollte speechSynthesis mit leerem Utterance "unlocked" werden
- **And** sollte ein kurzer Unlock-Ton gespielt werden
- **And** sollte sofort "Kamera-Unterstützung aktiviert" angesagt werden

### 3. Echtzeit-Kantenerkennung mit Audio-Feedback
- **Given** die Kamera läuft und Audio-Führung ist aktiv
- **When** ein Dokument ins Bild kommt
- **Then** sollte jscanify die Kanten in Echtzeit erkennen
- **And** sollte ein Erfolgston abgespielt werden
- **And** sollte "Dokumentränder erkannt. Halten Sie ruhig." angesagt werden
- **And** sollte ein kontinuierlicher Ton die Confidence-Level anzeigen (höhere Tonhöhe = bessere Erkennung)

### 4. Edge-Based Guidance (nicht direktional)
- **Given** Dokumentenkanten sind erkannt aber nicht optimal positioniert
- **When** Dokumentenecken zu nah am Bildrand sind
- **Then** sollte angesagt werden welche Kanten nicht sichtbar sind
- **And** sollte z.B. "Oberer Rand nicht sichtbar" statt "Kamera nach unten bewegen" sagen
- **And** sollte alle fehlenden Kanten auflisten (z.B. "Oberer Rand, Linker Rand nicht sichtbar")

### 5. Automatische Auslösung bei stabiler Erkennung
- **Given** Dokumentenkanten sind erkannt und zentriert
- **When** die Erkennung für 10 Frames (~1 Sekunde) stabil bleibt
- **Then** sollte ein Countdown gestartet werden ("2", "1")
- **And** sollte nach 2 Sekunden automatisch ausgelöst werden
- **And** sollte "Foto aufgenommen" angesagt werden
- **And** sollte ein Kamera-Auslöse-Sound gespielt werden

### 6. Auto-Crop und Perspektivkorrektur
- **Given** ein Foto wurde aufgenommen und Kanten wurden erkannt
- **When** das Foto verarbeitet wird
- **Then** sollte das Bild auf die erkannten Kanten zugeschnitten werden
- **And** sollte die Perspektive korrigiert werden (jscanify.extractPaper)
- **And** sollte hochauflösend sein (volle videoWidth/videoHeight)
- **And** sollte mit 90% JPEG-Qualität gespeichert werden

### 7. Teilweise Dokumentenerkennung (1/3 der Fläche)
- **Given** ein Dokument füllt nur 33% des Bildes
- **When** die Kantenerkennung läuft
- **Then** sollte das Dokument trotzdem erkannt werden (Threshold: 10-90%)
- **And** sollte Auto-Capture möglich sein
- **And** sollte Auto-Crop funktionieren

### 8. Hysterese zur Vermeidung von Flackern
- **Given** die Confidence schwankt um den Schwellwert
- **When** Kanten erkannt/verloren werden
- **Then** sollte Hysterese verwendet werden (Upper: 45%, Lower: 35%)
- **And** sollte nicht bei jedem Frame zwischen "erkannt" und "verloren" wechseln
- **And** sollte nur bei signifikanten Änderungen Ansagen machen

### 9. Page Reload Kompatibilität
- **Given** ein Benutzer lädt die Seite neu
- **When** AudioContext vom vorherigen Session existiert aber geschlossen ist
- **Then** sollte ein neuer AudioContext erstellt werden
- **And** sollte keine "Audiosystem not available" Fehlermeldung erscheinen
- **And** sollte Audio-Führung normal funktionieren

### 10. Mehrsprachigkeit (i18n)
- **Given** ein Benutzer wählt eine Sprache (de, en, es, fr)
- **When** Audio-Ansagen gemacht werden
- **Then** sollten alle Ansagen in der gewählten Sprache erfolgen
- **And** sollten Edge-Namen übersetzt sein ("Oberer Rand" / "Top edge" / "Borde superior" / "Bord supérieur")

---

## Definition of Done

- [x] jscanify v1.4.0 und OpenCV.js 4.7.0 über CDN geladen
- [x] AccessibleCameraAssistant Klasse implementiert
- [x] Screen Reader Auto-Detection (ARIA landmarks)
- [x] iOS Safari AudioContext + SpeechSynthesis Unlock
- [x] On-Demand Oscillator Pattern für iOS
- [x] Edge-Detection mit Hysterese (45%/35% Thresholds)
- [x] Auto-Capture nach 10 stabilen Frames
- [x] Auto-Crop mit Perspektivkorrektur
- [x] Edge-Based Guidance (nicht direktional)
- [x] Confidence-basierter kontinuierlicher Ton
- [x] Teilweise Dokumentenerkennung (10-90% Fläche)
- [x] Page Reload AudioContext Handling
- [x] i18n für 4 Sprachen (de, en, es, fr)
- [x] Alle Translations-Keys dokumentiert
- [x] Volume-Kontrolle und Test-Audio Button
- [x] Visuelle Indikatoren für Sehbehinderte (Farb-Overlay)
- [x] ARIA Live Regions für Screen Reader
- [x] Gherkin Feature mit Szenarien erstellt
- [x] User Story dokumentiert

---

## Technische Details

### Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    CameraManager                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │  AccessibleCameraAssistant                          │    │
│  │  ┌────────────┬──────────────┬──────────────────┐ │    │
│  │  │ Audio      │ Edge         │ Auto-Capture     │ │    │
│  │  │ System     │ Detection    │ & Auto-Crop      │ │    │
│  │  └────────────┴──────────────┴──────────────────┘ │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
┌──────────────┐  ┌──────────────┐   ┌──────────────┐
│ Web Audio    │  │ jscanify     │   │ OpenCV.js    │
│ API +        │  │ v1.4.0       │   │ 4.7.0        │
│ Speech       │  │              │   │              │
│ Synthesis    │  │ getEdges()   │   │ cv.imread()  │
│              │  │ extractPaper │   │ cv.imshow()  │
└──────────────┘  └──────────────┘   └──────────────┘
```

### Komponenten

#### AccessibleCameraAssistant Class
**Datei**: `src/pdfa/web_ui.html` (Zeilen 9300-10700)

**Eigenschaften**:
- `audioContext: AudioContext` - Web Audio API Kontext
- `synth: SpeechSynthesis` - Browser TTS Engine
- `scanner: jscanify.Scanner` - Edge Detection Library
- `analysisCanvas: HTMLCanvasElement` - 640x480 Analyse-Canvas
- `lastDetectedCorners` - Gespeicherte Ecken für Auto-Crop
- `edgeState: 'detected' | 'lost'` - Hysterese-Zustand
- `stableFrameCount: number` - Zähler für Auto-Capture
- `degradedMode: boolean` - Fallback wenn jscanify fehlschlägt

**Methoden**:
```javascript
// Initialization
async init()
async enable()
disable()
setupControls()

// Audio System
async playTone(frequency, duration)
playSuccessTone()
playWarningTone()
playContinuousFeedbackTone(confidence)
announce(text, priority)

// Edge Detection
async analyzeFrame()
calculateConfidence(result)
provideFeedback(confidence, result)
getMissingEdges(result)
isDocumentCentered(result)

// Auto-Capture
initiateAutoCapture()
performAutoCapture()
cancelAutoCapture()

// Auto-Crop
autoCropAndCorrect(canvas, corners) // in CameraManager
```

### Audio-System

#### Töne (Web Audio API)
```javascript
Erfolg: 880 Hz, 200ms (A5 - Kanten erkannt)
Warnung: 440 Hz, 150ms (A4 - Kanten verloren)
Kontinuierlich: 300-800 Hz (Confidence-abhängig)
Countdown: 523 Hz, 100ms (C5 - "2", "1")
Auslöser: 880 Hz + 440 Hz (Kamera-Shutter)
```

#### iOS Safari Spezialbehandlung
1. **AudioContext**: Muss in direktem User-Gesture erstellt und resumed werden
2. **SpeechSynthesis**: Muss mit leerem Utterance "unlocked" werden
3. **On-Demand Oscillators**: Jeder Ton erstellt eigenen Oscillator (kein Persistent)
4. **State Handling**: Check for `state === 'closed'` bei Page Reload

### Kantenerkennung

#### jscanify Integration
```javascript
// CDN laden mit Fallbacks
https://cdn.jsdelivr.net/npm/jscanify@1.4.0/dist/jscanify.min.js
https://unpkg.com/jscanify@1.4.0/dist/jscanify.min.js

// Scanner initialisieren
const scanner = new jscanify();

// Kanten erkennen
const result = scanner.findPaperContour(imageData);
// result.success: boolean
// result.corners: Array<{x, y}> (4 Ecken)

// Perspektivkorrektur
const corrected = scanner.extractPaper(mat, corners);
```

#### OpenCV.js Integration
```javascript
// Canvas zu Mat konvertieren
const mat = cv.imread(canvas);

// Mat zu Canvas konvertieren
cv.imshow(outputCanvas, mat);

// Cleanup (Memory Management)
mat.delete();
correctedImage.delete();
```

### Confidence-Berechnung

```javascript
function calculateConfidence(corners) {
  const area = calculatePolygonArea(corners);
  const areaRatio = area / canvasArea;

  // Accept 10-90% coverage (tolerant für Teilerfassung)
  if (areaRatio < 0.10 || areaRatio > 0.90) return 0;

  // Peak bei 40% (realistisch für gut zentriert)
  if (areaRatio <= 0.40) {
    // Linear von 0.25 (bei 10%) zu 1.0 (bei 40%)
    return 0.25 + (areaRatio - 0.10) * (0.75 / 0.30);
  } else {
    // Linear von 1.0 (bei 40%) zu 0.5 (bei 90%)
    return 1.0 - (areaRatio - 0.40) * (0.5 / 0.50);
  }
}
```

### Hysterese-Pattern

```javascript
const upperThreshold = 0.45; // Schwelle für lost → detected
const lowerThreshold = 0.35; // Schwelle für detected → lost

const isDetected = wasDetected
  ? confidence >= lowerThreshold  // Bleib detected bis < 35%
  : confidence >= upperThreshold;  // Werde detected ab >= 45%
```

### Auto-Crop Workflow

```
1. Video Frame → Full Resolution Canvas (videoWidth × videoHeight)
2. Prüfe: Sind Ecken gespeichert? (lastDetectedCorners)
3. Skaliere Ecken: Analysis Canvas (640×480) → Full Resolution
4. cv.imread(canvas) → Mat
5. scanner.extractPaper(mat, scaledCorners) → Korrigiertes Mat
6. cv.imshow(outputCanvas, correctedMat) → Canvas
7. canvas.toDataURL('image/jpeg', 0.90) → High-Quality JPEG
8. mat.delete(), correctedMat.delete() → Cleanup
```

### i18n Translations

**Neue Keys (US-008)**:
```javascript
'camera.a11y.topEdge': 'Oberer Rand' / 'Top edge' / ...
'camera.a11y.bottomEdge': 'Unterer Rand' / 'Bottom edge' / ...
'camera.a11y.leftEdge': 'Linker Rand' / 'Left edge' / ...
'camera.a11y.rightEdge': 'Rechter Rand' / 'Right edge' / ...
'camera.a11y.notVisible': 'nicht sichtbar' / 'not visible' / ...
```

**Bestehende Keys**:
```javascript
'camera.a11y.enabled': 'Kamera-Unterstützung aktiviert'
'camera.a11y.edgesDetected': 'Dokumentränder erkannt. Halten Sie ruhig.'
'camera.a11y.edgesLost': 'Ränder verloren. Kameraposition anpassen.'
'camera.a11y.moveCloser': 'Näher ans Dokument'
'camera.a11y.moveFarther': 'Weiter weg vom Dokument'
'camera.a11y.centerDocument': 'Dokument zentrieren'
'camera.a11y.holdSteady': 'Kamera ruhig halten'
'camera.a11y.photoCaptured': 'Foto aufgenommen'
```

### Deployment

**Client-Side Only** (kein Backend erforderlich):
- Feature aktiviert sich bei Screen Reader Detection
- Alle Libraries über CDN geladen (jscanify, OpenCV.js)
- Browser-Anforderungen:
  - Web Audio API Support
  - Speech Synthesis API Support (optional, degrades gracefully)
  - getUserMedia() für Kamera
  - Canvas 2D Context
  - ES6+ JavaScript

**Performance**:
- Frame Analysis: ~10 FPS (100ms Intervall)
- Analyse Canvas: 640×480 (Performance-optimiert)
- Capture Canvas: Full videoWidth/videoHeight (Qualitäts-optimiert)
- Memory Management: Alle cv.Mat werden explizit mit .delete() freigegeben

---

## Risiken & Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| iOS Safari blockiert Audio | Mittel | Hoch | ✅ AudioContext + SpeechSynthesis Unlock in User-Gesture |
| jscanify CDN nicht erreichbar | Niedrig | Hoch | ✅ Degraded Mode: Audio ohne Edge Detection |
| Falsche Kantenerkennung | Mittel | Mittel | ✅ Confidence Threshold + Hysterese + Manuelle Korrektur möglich |
| OpenCV.js zu groß (8MB) | Niedrig | Niedrig | ✅ Lazy Loading nur wenn Feature aktiviert |
| Screen Reader Interferenz | Mittel | Mittel | ✅ ARIA Live Regions + Throttled Announcements |
| Battery Drain (Continuous Analysis) | Niedrig | Niedrig | ✅ 10 FPS statt 30 FPS, Analysis Canvas 640×480 |
| Memory Leaks (cv.Mat) | Mittel | Hoch | ✅ Explizites .delete() in try-finally Blöcken |

---

## Verwandte Spezifikationen

**User Stories**:
- Keine (standalone Feature)

**Gherkin Features**:
- [Accessibility Camera Assistance](../features/gherkin-accessibility-camera-assistance.feature) (31 Szenarien)

**Dokumentation**:
- [ACCESSIBILITY.md](../../ACCESSIBILITY.md)
- [AGENTS.md](../../../AGENTS.md)
- [TRANSLATIONS.md](../../../TRANSLATIONS.md)

**External Specs**:
- [WCAG 2.1 Level AA](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA 1.2](https://www.w3.org/TR/wai-aria-1.2/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [Speech Synthesis API](https://developer.mozilla.org/en-US/docs/Web/API/SpeechSynthesis)
- [jscanify Documentation](https://www.npmjs.com/package/jscanify)
- [OpenCV.js Documentation](https://docs.opencv.org/4.7.0/d5/d10/tutorial_js_root.html)

---

## Änderungshistorie

| Datum | Version | Änderung | Commits |
|-------|---------|----------|---------|
| 2026-01-01 | 1.0 | Initiale Erstellung nach vollständiger Implementierung | 2e10297, 1e07b3c, 420d874, f523eee, ed0b81b |
| 2026-01-01 | 1.0 | iOS Safari TTS Fix, Partial Document Support, Edge-Based Guidance | 2e10297 |
| 2026-01-01 | 1.0 | iOS Audio Fix, Instant TTS Feedback, Auto-Crop Feature | 1e07b3c |
| 2025-12-31 | 1.0 | iOS Safari Audio Tones Fix (On-Demand Oscillators) | 420d874 |
| 2025-12-31 | 1.0 | Hysteresis und Contextual Feedback für Edge Detection | f523eee |
| 2025-12-31 | 1.0 | i18n Translations und Auto-Capture Corner Validation | ed0b81b |

---

**Feature Owner**: PDF/A Service Team
**Stakeholders**: Blinde und sehbehinderte Benutzer, Compliance Team
**Priority**: Hoch (Legal Requirement - WCAG 2.1 AA)
**Complexity**: Hoch (Audio APIs, Computer Vision, iOS Quirks)
**Estimated Effort**: 5-8 Tage (bereits implementiert)

---

## INVEST Check ✅

- ✅ **I**ndependent - Standalone Feature, keine Dependencies zu anderen Stories
- ✅ **N**egotiable - Core Features fix, UX Details iterativ verbessert
- ✅ **V**aluable - Ermöglicht neuen Benutzersegment (Blinde) Service-Nutzung
- ✅ **E**stimable - Klar definierter Scope, Technologie bekannt
- ✅ **S**mall - In einer Iteration implementierbar (5-8 Tage)
- ✅ **T**estable - Klare Akzeptanzkriterien, Gherkin Szenarien vorhanden
