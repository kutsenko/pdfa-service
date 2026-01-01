# language: de
Funktionalität: Barrierefreie Kamera-Unterstützung für Blinde
  Als blinder oder sehbehinderter Benutzer
  möchte ich Dokumente mittels Audio-Führung fotografieren können
  damit ich ohne visuelle Kontrolle hochwertige Dokumentenscans erstellen kann

  Hintergrund:
    Angenommen der Benutzer öffnet die Kamera-Seite
    Und der Browser unterstützt Web Audio API
    Und der Browser unterstützt getUserMedia

  # ============================================================================
  # Feature 1: Screen Reader Auto-Detection & Initialization
  # ============================================================================

  Szenario: Screen Reader wird automatisch erkannt und Feature aktiviert
    Angenommen ein Screen Reader ist aktiv (VoiceOver, NVDA, JAWS)
    Wenn die Kamera-Seite geladen wird
    Dann sollte die Accessibility-Checkbox automatisch aktiviert werden
    Und die Audio-Führung sollte initialisiert werden
    Und eine Sprachansage "Camera assistance enabled" sollte erfolgen

  Szenario: Kein Screen Reader erkannt - Feature bleibt deaktiviert
    Angenommen kein Screen Reader ist aktiv
    Wenn die Kamera-Seite geladen wird
    Dann sollte die Accessibility-Checkbox deaktiviert bleiben
    Und keine automatische Initialisierung erfolgen

  Szenario: Manuelle Aktivierung ohne Screen Reader
    Angenommen kein Screen Reader ist aktiv
    Und die Accessibility-Checkbox ist deaktiviert
    Wenn der Benutzer die Checkbox aktiviert
    Dann sollte die Audio-Führung initialisiert werden
    Und eine Sprachansage "Kamera-Unterstützung aktiviert" sollte erfolgen

  # ============================================================================
  # Feature 2: iOS Safari Audio/TTS Unlock
  # ============================================================================

  Szenario: iOS Safari AudioContext Unlock in User-Gesture
    Angenommen der Benutzer verwendet iOS Safari
    Und die Accessibility-Checkbox ist deaktiviert
    Wenn der Benutzer die Checkbox aktiviert
    Dann sollte AudioContext im direkten User-Gesture erstellt werden
    Und AudioContext sollte sofort resumed werden
    Und der AudioContext State sollte "running" sein
    Und keine "AudioContext not available" Fehlermeldung sollte erscheinen

  Szenario: iOS Safari SpeechSynthesis Unlock
    Angenommen der Benutzer verwendet iOS Safari
    Und die Accessibility-Checkbox ist deaktiviert
    Wenn der Benutzer die Checkbox aktiviert
    Dann sollte speechSynthesis.cancel() aufgerufen werden
    Und ein leeres SpeechSynthesisUtterance sollte gesprochen werden
    Und nachfolgende Sprachansagen sollten funktionieren

  Szenario: iOS Safari Unlock-Ton wird gespielt
    Angenommen der Benutzer verwendet iOS Safari
    Und die Accessibility-Checkbox ist deaktiviert
    Wenn der Benutzer die Checkbox aktiviert
    Dann sollte ein kurzer Unlock-Ton (440 Hz, 50ms) gespielt werden
    Und der Audio-Pipeline sollte entsperrt sein

  Szenario: Sofortige TTS-Ansage vor Library-Loading
    Angenommen der Benutzer aktiviert die Audio-Führung
    Wenn das AudioContext-Unlock abgeschlossen ist
    Dann sollte sofort "Kamera-Unterstützung aktiviert" angesagt werden
    Und die Ansage sollte VOR dem jscanify-Loading erfolgen
    Und der Benutzer sollte nicht auf Library-Download warten

  # ============================================================================
  # Feature 3: Page Reload AudioContext Handling
  # ============================================================================

  Szenario: AudioContext nach Page Reload ist geschlossen
    Angenommen der Benutzer hatte Audio-Führung aktiviert
    Und die Seite wird neu geladen
    Wenn der AudioContext State "closed" ist
    Dann sollte ein neuer AudioContext erstellt werden
    Und keine "Audiosystem not available" Fehlermeldung erscheinen
    Und Audio-Führung sollte normal funktionieren

  Szenario: AudioContext existiert aber ist suspended
    Angenommen der AudioContext existiert aber ist suspended
    Wenn der Benutzer Audio-Führung aktiviert
    Dann sollte der bestehende AudioContext resumed werden
    Und kein neuer AudioContext erstellt werden

  # ============================================================================
  # Feature 4: Edge Detection mit jscanify
  # ============================================================================

  Szenario: jscanify lädt erfolgreich von CDN
    Angenommen Audio-Führung wird aktiviert
    Wenn jscanify von CDN geladen wird
    Dann sollte jscanify.Scanner initialisiert werden
    Und degradedMode sollte false sein
    Und Edge Detection sollte verfügbar sein

  Szenario: jscanify CDN fehlgeschlagen - Degraded Mode
    Angenommen Audio-Führung wird aktiviert
    Wenn alle jscanify CDN-URLs fehlschlagen
    Dann sollte degradedMode auf true gesetzt werden
    Und eine Warnung sollte in Console ausgegeben werden
    Und Audio-Töne sollten weiterhin funktionieren
    Aber Edge Detection sollte nicht verfügbar sein

  Szenario: OpenCV.js lädt erfolgreich
    Angenommen Audio-Führung wird aktiviert
    Und jscanify ist geladen
    Wenn OpenCV.js von CDN geladen wird
    Dann sollte window.cv verfügbar sein
    Und cv.imread und cv.imshow sollten funktionieren

  Szenario: Kanten werden in Echtzeit erkannt
    Angenommen Audio-Führung ist aktiv
    Und ein Dokument ist im Kamerabild
    Wenn analyzeFrame() läuft
    Dann sollte jscanify.findPaperContour() aufgerufen werden
    Und result.success sollte true sein
    Und result.corners sollte 4 Ecken enthalten
    Und jede Ecke sollte x und y Koordinaten haben

  # ============================================================================
  # Feature 5: Confidence-Berechnung mit Teilerfassung
  # ============================================================================

  Szenario: Dokument füllt 40% der Fläche - Optimale Confidence
    Angenommen Dokumentenkanten sind erkannt
    Wenn das Dokument 40% der Canvas-Fläche füllt
    Dann sollte die Confidence 1.0 (100%) sein

  Szenario: Dokument füllt 33% der Fläche - Akzeptable Confidence
    Angenommen Dokumentenkanten sind erkannt
    Wenn das Dokument 33% der Canvas-Fläche füllt
    Dann sollte die Confidence > 0.5 sein
    Und Auto-Capture sollte möglich sein

  Szenario: Dokument füllt 10% der Fläche - Minimale Confidence
    Angenommen Dokumentenkanten sind erkannt
    Wenn das Dokument 10% der Canvas-Fläche füllt
    Dann sollte die Confidence ≈ 0.25 sein
    Und Edge Detection sollte funktionieren

  Szenario: Dokument füllt 5% der Fläche - Zu klein
    Angenommen ein sehr kleines Objekt ist im Bild
    Wenn das Objekt nur 5% der Canvas-Fläche füllt
    Dann sollte die Confidence 0 sein
    Und keine Kantenerkennung erfolgen

  Szenario: Dokument füllt 95% der Fläche - Zu nah
    Angenommen das Dokument ist zu nah an der Kamera
    Wenn das Dokument 95% der Canvas-Fläche füllt
    Dann sollte die Confidence 0 sein
    Und "Weiter weg vom Dokument" sollte angesagt werden

  # ============================================================================
  # Feature 6: Hysterese zur Flacker-Vermeidung
  # ============================================================================

  Szenario: Confidence steigt über Upper Threshold - Transition zu "detected"
    Angenommen edgeState ist "lost"
    Und die Confidence ist 0.30
    Wenn die Confidence auf 0.45 steigt
    Dann sollte edgeState zu "detected" wechseln
    Und ein Erfolgston (880 Hz) sollte gespielt werden
    Und "Dokumentränder erkannt" sollte angesagt werden

  Szenario: Confidence schwankt um 40% - Bleibt "detected" (Hysterese)
    Angenommen edgeState ist "detected"
    Und die Confidence ist 0.45
    Wenn die Confidence auf 0.38 sinkt (zwischen 35% und 45%)
    Dann sollte edgeState "detected" bleiben
    Und keine Statusänderung erfolgen
    Und kein Warnton gespielt werden

  Szenario: Confidence fällt unter Lower Threshold - Transition zu "lost"
    Angenommen edgeState ist "detected"
    Und die Confidence ist 0.38
    Wenn die Confidence auf 0.33 fällt
    Dann sollte edgeState zu "lost" wechseln
    Und ein Warnton (440 Hz) sollte gespielt werden
    Und "Ränder verloren. Kameraposition anpassen." sollte angesagt werden

  # ============================================================================
  # Feature 7: Audio-Feedback (Töne + TTS)
  # ============================================================================

  Szenario: Erfolgston bei Kantenerkennung
    Angenommen Kanten werden erstmalig erkannt
    Wenn edgeState zu "detected" wechselt
    Dann sollte ein Erfolgston (880 Hz, 200ms) gespielt werden

  Szenario: Warnton bei Kanten verloren
    Angenommen edgeState wechselt zu "lost"
    Wenn Kanten verloren gehen
    Dann sollte ein Warnton (440 Hz, 150ms) gespielt werden

  Szenario: Kontinuierlicher Ton zeigt Confidence an
    Angenommen edgeState ist "detected"
    Und Confidence ist 0.8
    Wenn kontinuierliches Feedback läuft
    Dann sollte Tonhöhe confidence-abhängig sein (300-800 Hz)
    Und höhere Confidence sollte höhere Tonhöhe erzeugen

  Szenario: TTS-Ansage wird gedrosselt (Throttling)
    Angenommen eine Ansage wurde vor 1 Sekunde gemacht
    Wenn eine neue Ansage angefordert wird (priority != 'force')
    Dann sollte die Ansage unterdrückt werden
    Und announcementThrottle (2000ms) sollte eingehalten werden

  Szenario: Force-Priority Ansage umgeht Throttling
    Angenommen eine Ansage wurde vor 1 Sekunde gemacht
    Wenn eine Ansage mit priority='force' angefordert wird
    Dann sollte die Ansage sofort erfolgen
    Und Throttling sollte umgangen werden

  # ============================================================================
  # Feature 8: Edge-Based Guidance (nicht direktional)
  # ============================================================================

  Szenario: Oberer Rand zu nah am Bildrand
    Angenommen Kanten sind erkannt
    Wenn eine Dokumentenecke y < 20 hat
    Dann sollte getMissingEdges() "Oberer Rand" zurückgeben
    Und "Oberer Rand nicht sichtbar" sollte angesagt werden

  Szenario: Mehrere Ränder nicht sichtbar
    Angenommen Kanten sind erkannt
    Wenn Ecken bei x < 20 und y > 460 sind (640x480 Canvas)
    Dann sollte getMissingEdges() ["Linker Rand", "Unterer Rand"] zurückgeben
    Und "Linker Rand, Unterer Rand nicht sichtbar" sollte angesagt werden

  Szenario: Alle Ränder sichtbar - Zentriertes Dokument
    Angenommen Kanten sind erkannt
    Wenn alle Ecken > 20px vom Rand entfernt sind
    Dann sollte getMissingEdges() leeres Array zurückgeben
    Und isDocumentCentered() sollte true zurückgeben
    Und keine Edge-Warnings sollten erfolgen

  Szenario: Periodisches Guidance-Update (alle 10 Sekunden)
    Angenommen Kanten sind erkannt aber nicht zentriert
    Und lastStatusTime ist 11 Sekunden her
    Wenn provideFeedback() läuft
    Dann sollten fehlende Ränder angesagt werden
    Und lastStatusTime sollte aktualisiert werden

  # ============================================================================
  # Feature 9: Auto-Capture bei stabiler Erkennung
  # ============================================================================

  Szenario: Stabilitätszähler inkrementiert bei gutem Frame
    Angenommen edgeState ist "detected"
    Und Dokument ist zentriert
    Und Auto-Capture ist aktiviert
    Wenn ein stabiler Frame erkannt wird
    Dann sollte stableFrameCount um 1 erhöht werden

  Szenario: Auto-Capture Countdown startet nach 10 stabilen Frames
    Angenommen stableFrameCount erreicht 10
    Und Auto-Capture ist aktiviert
    Wenn der nächste stabile Frame kommt
    Dann sollte initiateAutoCapture() aufgerufen werden
    Und "Kamera ruhig halten" sollte angesagt werden
    Und ein 2-Sekunden Countdown sollte starten

  Szenario: Countdown-Ansagen "2", "1"
    Angenommen Auto-Capture Countdown läuft
    Wenn jede Sekunde vergeht
    Dann sollte ein Beep (523 Hz, 100ms) gespielt werden
    Und "2" bzw. "1" sollte angesagt werden

  Szenario: Foto wird nach Countdown aufgenommen
    Angenommen Countdown ist abgelaufen
    Wenn performAutoCapture() ausgeführt wird
    Dann sollte ein Kamera-Shutter-Ton gespielt werden (880 Hz + 440 Hz)
    Und "Foto aufgenommen" sollte angesagt werden
    Und cameraManager.capturePhoto() sollte aufgerufen werden

  Szenario: Auto-Capture wird abgebrochen bei Kanten-Verlust
    Angenommen Countdown läuft
    Wenn Kanten verloren gehen (edgeState → "lost")
    Dann sollte cancelAutoCapture() aufgerufen werden
    Und Countdown sollte gestoppt werden
    Und stableFrameCount sollte auf 0 zurückgesetzt werden

  # ============================================================================
  # Feature 10: Auto-Crop und Perspektivkorrektur
  # ============================================================================

  Szenario: lastDetectedCorners werden beim Frame-Analyse gespeichert
    Angenommen analyzeFrame() erkennt Kanten
    Wenn Ecken extrahiert werden
    Dann sollte lastDetectedCorners aktualisiert werden
    Und Ecken sollten für Auto-Crop verfügbar sein

  Szenario: Auto-Crop wird angewendet wenn Ecken verfügbar
    Angenommen capturePhoto() wird aufgerufen
    Und lastDetectedCorners ist gesetzt
    Und degradedMode ist false
    Wenn das Foto verarbeitet wird
    Dann sollte autoCropAndCorrect() aufgerufen werden
    Und Ecken sollten von Analysis-Canvas auf Full-Resolution skaliert werden

  Szenario: Ecken-Skalierung von 640x480 auf Full-Resolution
    Angenommen Analysis-Canvas ist 640x480
    Und Video-Resolution ist 1920x1080
    Wenn Ecken {x: 320, y: 240} sind
    Dann sollten skalierte Ecken {x: 960, y: 540} sein (3x Faktor)

  Szenario: OpenCV.js Perspektivkorrektur
    Angenommen autoCropAndCorrect() läuft
    Und skalierte Ecken sind berechnet
    Wenn cv.imread(canvas) ausgeführt wird
    Dann sollte ein cv.Mat erstellt werden
    Und scanner.extractPaper(mat, corners) sollte aufgerufen werden
    Und ein perspektivkorrigiertes Mat sollte zurückgegeben werden

  Szenario: Mat zu Canvas Konvertierung und Cleanup
    Angenommen extractPaper() hat korrigiertes Mat zurückgegeben
    Wenn cv.imshow(outputCanvas, correctedMat) ausgeführt wird
    Dann sollte outputCanvas das korrigierte Bild enthalten
    Und mat.delete() sollte aufgerufen werden (Memory Cleanup)
    Und correctedImage.delete() sollte aufgerufen werden

  Szenario: High-Quality JPEG für Auto-Crop Bilder
    Angenommen Auto-Crop war erfolgreich
    Wenn outputCanvas.toDataURL() aufgerufen wird
    Dann sollte JPEG-Qualität 90% sein
    Und Bild sollte höhere Qualität haben als nicht-gecroppt (85%)

  Szenario: Fallback bei Auto-Crop Fehler
    Angenommen autoCropAndCorrect() schlägt fehl (Exception)
    Wenn ein Fehler während Perspektivkorrektur auftritt
    Dann sollte Original-Canvas verwendet werden
    Und canvas.toDataURL('image/jpeg', 0.85) sollte zurückgegeben werden
    Und Fehler sollte in Console geloggt werden

  # ============================================================================
  # Feature 11: Mehrsprachigkeit (i18n)
  # ============================================================================

  Szenario: Deutsche Ansagen
    Angenommen window.currentLang ist "de"
    Wenn Audio-Ansagen gemacht werden
    Dann sollten Ansagen auf Deutsch erfolgen
    Und "Oberer Rand nicht sichtbar" sollte angesagt werden
    Und speechSynthesis.lang sollte "de-DE" sein

  Szenario: Englische Ansagen
    Angenommen window.currentLang ist "en"
    Wenn Audio-Ansagen gemacht werden
    Dann sollten Ansagen auf Englisch erfolgen
    Und "Top edge not visible" sollte angesagt werden
    Und speechSynthesis.lang sollte "en-US" sein

  Szenario: Spanische Ansagen
    Angenommen window.currentLang ist "es"
    Wenn Audio-Ansagen gemacht werden
    Dann sollten Ansagen auf Spanisch erfolgen
    Und "Borde superior no visible" sollte angesagt werden
    Und speechSynthesis.lang sollte "es-ES" sein

  Szenario: Französische Ansagen
    Angenommen window.currentLang ist "fr"
    Wenn Audio-Ansagen gemacht werden
    Dann sollten Ansagen auf Französisch erfolgen
    Und "Bord supérieur non visible" sollte angesagt werden
    Und speechSynthesis.lang sollte "fr-FR" sein

  # ============================================================================
  # Feature 12: Visuelle Indikatoren für Sehbehinderte
  # ============================================================================

  Szenario: Grüner Overlay bei erfolgreicher Erkennung
    Angenommen Kanten werden erkannt
    Wenn showVisualIndicator('success') aufgerufen wird
    Dann sollte ein grüner Farb-Overlay angezeigt werden
    Und Overlay sollte nach 500ms verschwinden

  Szenario: Gelber Overlay bei Warnung
    Angenommen Kanten gehen verloren
    Wenn showVisualIndicator('warning') aufgerufen wird
    Dann sollte ein gelber Farb-Overlay angezeigt werden
    Und Overlay sollte nach 500ms verschwinden

  # ============================================================================
  # Feature 13: ARIA Live Regions für Screen Reader
  # ============================================================================

  Szenario: ARIA Live Region wird aktualisiert
    Angenommen ein Screen Reader ist aktiv
    Wenn announce() aufgerufen wird
    Dann sollte <div id="srAnnouncements"> aktualisiert werden
    Und Screen Reader sollte Text vorlesen
    Und aria-live="polite" sollte eingehalten werden

  # ============================================================================
  # Feature 14: Volume-Kontrolle
  # ============================================================================

  Szenario: Volume-Slider ändert Lautstärke
    Angenommen Audio-Führung ist aktiv
    Wenn Volume-Slider auf 50% gesetzt wird
    Dann sollte this.volume auf 0.5 gesetzt werden
    Und GainNode.gain sollte 0.5 * 0.3 sein (30% max für Töne)
    Und SpeechSynthesisUtterance.volume sollte 0.5 sein

  # ============================================================================
  # Feature 15: Test-Audio Button
  # ============================================================================

  Szenario: Test-Audio spielt Ton und TTS
    Angenommen Audio-Führung ist aktiv
    Wenn "Test Audio" Button geklickt wird
    Dann sollte testAudio() aufgerufen werden
    Und ein Erfolgston sollte gespielt werden
    Und "Audio test. If you can hear this, audio is working." sollte angesagt werden

  # ============================================================================
  # Feature 16: Disable Feature
  # ============================================================================

  Szenario: Audio-Führung wird deaktiviert
    Angenommen Audio-Führung ist aktiv
    Wenn Checkbox deaktiviert wird
    Dann sollte disable() aufgerufen werden
    Und analysisLoopId sollte gestoppt werden (clearInterval)
    Und "Kamera-Unterstützung deaktiviert" sollte angesagt werden
    Und enabled sollte false sein

  Szenario: AudioContext wird bei Deaktivierung geschlossen
    Angenommen Audio-Führung ist aktiv
    Wenn disable() aufgerufen wird
    Dann sollte AudioContext.close() aufgerufen werden
    Und audioContext sollte auf null gesetzt werden

  # ============================================================================
  # Feature 17: Error Handling
  # ============================================================================

  Szenario: Browser unterstützt keine Web Audio API
    Angenommen window.AudioContext ist undefined
    Wenn Audio-Führung aktiviert wird
    Dann sollte ein Fehler geworfen werden
    Und "AudioContext not supported in this browser" sollte die Fehlermeldung sein
    Und Checkbox sollte deaktiviert werden

  Szenario: getUserMedia fehlgeschlagen
    Angenommen Kamera-Permission wird verweigert
    Wenn Kamera-Zugriff angefordert wird
    Dann sollte CameraManager einen Fehler werfen
    Aber Audio-Führung sollte trotzdem initialisiert werden können

  Szenario: Canvas 2D Context Fehler
    Angenommen Canvas.getContext('2d') schlägt fehl
    Wenn Analysis-Canvas erstellt wird
    Dann sollte ein Fehler geworfen werden
    Und "Failed to create canvas 2d context" sollte die Fehlermeldung sein

  # ============================================================================
  # Feature 18: Performance & Memory
  # ============================================================================

  Szenario: Frame-Analyse läuft mit 10 FPS
    Angenommen Audio-Führung ist aktiv
    Wenn startAnalysis() aufgerufen wird
    Dann sollte analysisLoopId ein Intervall von 100ms haben
    Und analyzeFrame() sollte alle 100ms aufgerufen werden

  Szenario: Analysis-Canvas ist Performance-optimiert
    Angenommen analyzeFrame() läuft
    Wenn Video-Frame auf Canvas gezeichnet wird
    Dann sollte Analysis-Canvas 640x480 Pixel sein (nicht Full-Resolution)
    Und Performance sollte auf älteren Geräten akzeptabel sein

  Szenario: Capture-Canvas nutzt Full-Resolution für Qualität
    Angenommen capturePhoto() wird aufgerufen
    Wenn Video-Frame erfasst wird
    Dann sollte Capture-Canvas video.videoWidth × video.videoHeight sein
    Und maximale Qualität sollte gewährleistet sein

  Szenario: OpenCV Mat wird explizit freigegeben
    Angenommen autoCropAndCorrect() wird aufgerufen
    Wenn cv.Mat Objekte erstellt werden
    Dann sollte mat.delete() in finally-Block aufgerufen werden
    Und correctedImage.delete() sollte ebenfalls aufgerufen werden
    Und keine Memory-Leaks sollten entstehen
