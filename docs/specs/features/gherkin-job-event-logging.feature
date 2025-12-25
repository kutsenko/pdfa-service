# language: de
Funktionalität: Detaillierte Event-Protokollierung für Konvertierungsaufträge
  Als Benutzer des PDF/A-Service
  möchte ich eine vollständige Event-Liste für jeden Auftrag
  damit ich die Konvertierungsentscheidungen nachvollziehen kann

  Hintergrund:
    Angenommen MongoDB ist verbunden
    Und ein Benutzer "test@example.com" ist authentifiziert

  # =============================================================================
  # Szenario-Gruppe 1: OCR-Entscheidung
  # =============================================================================

  Szenario: OCR wird übersprungen wegen Tagged-PDF (Office-Dokument)
    Angenommen eine Office-Datei "presentation.pptx" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter               | Wert  |
      | pdfa_level             | 2     |
      | ocr_enabled            | true  |
      | skip_ocr_on_tagged_pdfs| true  |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "source_format": "pptx",
          "target_format": "pdf",
          "conversion_required": true,
          "converter": "office_to_pdf"
        }
        """
    Und es sollte ein Event mit Typ "ocr_decision" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "decision": "skip",
          "reason": "tagged_pdf",
          "has_struct_tree_root": true
        }
        """
    Und es sollte ein Event mit Typ "compression_selected" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "profile": "preserve",
          "reason": "auto_switched_for_tagged_pdf"
        }
        """

  Szenario: OCR wird übersprungen wegen vorhandenem Text
    Angenommen eine PDF-Datei "document.pdf" wird hochgeladen
    Und die PDF hat Text auf 3 von 3 Seiten mit insgesamt 1523 Zeichen
    Und die Konfiguration ist:
      | Parameter               | Wert  |
      | pdfa_level             | 2     |
      | ocr_enabled            | true  |
      | skip_ocr_on_tagged_pdfs| true  |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "source_format": "pdf",
          "target_format": "pdf",
          "conversion_required": false
        }
        """
    Und es sollte ein Event mit Typ "ocr_decision" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "decision": "skip",
          "reason": "has_text",
          "pages_with_text": 3,
          "total_pages_checked": 3,
          "text_ratio": 1.0,
          "total_characters": 1523
        }
        """

  Szenario: OCR wird durchgeführt wegen fehlendem Text
    Angenommen eine gescannte PDF-Datei "scan.pdf" wird hochgeladen
    Und die PDF hat Text auf 0 von 3 Seiten mit insgesamt 8 Zeichen
    Und die Konfiguration ist:
      | Parameter               | Wert  |
      | pdfa_level             | 2     |
      | ocr_enabled            | true  |
      | skip_ocr_on_tagged_pdfs| true  |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
    Und es sollte ein Event mit Typ "ocr_decision" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "decision": "perform",
          "reason": "no_text",
          "pages_with_text": 0,
          "total_pages_checked": 3,
          "text_ratio": 0.0,
          "total_characters": 8
        }
        """

  # =============================================================================
  # Szenario-Gruppe 2: Format-Konvertierung
  # =============================================================================

  Szenario: Office-Dokument wird zu PDF konvertiert
    Angenommen eine Word-Datei "report.docx" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter  | Wert |
      | pdfa_level | 2    |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "source_format": "docx",
          "target_format": "pdf",
          "conversion_required": true,
          "converter": "office_to_pdf"
        }
        """
      Und das Event sollte "conversion_time_seconds" enthalten

  Szenario: Bild wird zu PDF konvertiert
    Angenommen eine Bilddatei "photo.jpg" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter  | Wert |
      | pdfa_level | 2    |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "source_format": "jpg",
          "target_format": "pdf",
          "conversion_required": true,
          "converter": "image_to_pdf"
        }
        """
      Und das Event sollte "conversion_time_seconds" enthalten

  Szenario: PDF benötigt keine Format-Konvertierung
    Angenommen eine PDF-Datei "document.pdf" wird hochgeladen
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "format_conversion" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "source_format": "pdf",
          "target_format": "pdf",
          "conversion_required": false
        }
        """

  # =============================================================================
  # Szenario-Gruppe 3: Fallback-Mechanismen
  # =============================================================================

  Szenario: Tier 2 Fallback bei Ghostscript-Fehler
    Angenommen eine problematische PDF-Datei "problematic.pdf" wird hochgeladen
    Und OCRmyPDF schlägt mit Ghostscript-Fehler fehl
    Und die Konfiguration ist:
      | Parameter  | Wert |
      | pdfa_level | 3    |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "fallback_applied" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "tier": 2,
          "reason": "ghostscript_error"
        }
        """
      Und das Event sollte "original_error" enthalten
      Und das Event sollte "safe_mode_config" enthalten
      Und das Event sollte "pdfa_level_downgrade" enthalten mit:
        """
        {
          "original": "3",
          "fallback": "2"
        }
        """

  Szenario: Tier 3 Fallback (kein OCR) nach Tier 2 Fehler
    Angenommen eine sehr problematische PDF-Datei "very-problematic.pdf" wird hochgeladen
    Und Tier 2 Fallback schlägt ebenfalls fehl
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "fallback_applied" existieren mit Tier 2
    Und es sollte ein weiteres Event mit Typ "fallback_applied" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "tier": 3,
          "reason": "tier2_failed",
          "ocr_disabled": true
        }
        """
      Und das Event sollte "tier2_error" enthalten
      Und das Event sollte "safe_mode_config" enthalten

  Szenario: Keine Fallbacks bei erfolgreicher Standardkonvertierung
    Angenommen eine normale PDF-Datei "normal.pdf" wird hochgeladen
    Wenn der Konvertierungsjob erfolgreich ausgeführt wird
    Dann sollte KEIN Event mit Typ "fallback_applied" existieren

  # =============================================================================
  # Szenario-Gruppe 4: Pass-through-Modus
  # =============================================================================

  Szenario: Pass-through-Modus für PDF-Ausgabe ohne OCR
    Angenommen eine Office-Datei "document.docx" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter   | Wert  |
      | pdfa_level  | pdf   |
      | ocr_enabled | false |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "passthrough_mode" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "enabled": true,
          "reason": "pdf_output_no_ocr",
          "pdfa_level": "pdf",
          "ocr_enabled": false
        }
        """

  Szenario: Pass-through-Modus mit Tag-Erhaltung
    Angenommen eine Office-Datei "presentation.pptx" wird hochgeladen
    Und das Office-Dokument enthält Struktur-Tags
    Und die Konfiguration ist:
      | Parameter   | Wert  |
      | pdfa_level  | pdf   |
      | ocr_enabled | false |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "passthrough_mode" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "enabled": true,
          "has_tags": true,
          "tags_preserved": true
        }
        """

  # =============================================================================
  # Szenario-Gruppe 5: Kompressionsprofilwahl
  # =============================================================================

  Szenario: Benutzer wählt Quality-Profil
    Angenommen eine PDF-Datei "document.pdf" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter            | Wert    |
      | compression_profile  | quality |
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte ein Event mit Typ "compression_selected" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "profile": "quality",
          "reason": "user_selected"
        }
        """
      Und das Event sollte "settings" enthalten mit:
        """
        {
          "image_dpi": 300,
          "jpg_quality": 95,
          "optimize": 1
        }
        """

  Szenario: Auto-Switch zu Preserve-Profil für Tagged-PDF
    Angenommen eine Office-Datei "presentation.pptx" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter            | Wert     |
      | compression_profile  | balanced |
      | skip_ocr_on_tagged_pdfs | true  |
    Wenn der Konvertierungsjob ausgeführt wird
    Und das Dokument Tagged-PDF erzeugt
    Dann sollte ein Event mit Typ "compression_selected" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "profile": "preserve",
          "reason": "auto_switched_for_tagged_pdf",
          "original_profile": "balanced"
        }
        """
      Und das Event sollte "settings" enthalten mit:
        """
        {
          "remove_vectors": false
        }
        """

  # =============================================================================
  # Szenario-Gruppe 6: Job-Lifecycle-Events
  # =============================================================================

  Szenario: Job-Timeout wird protokolliert
    Angenommen ein Job wird gestartet
    Und der Job läuft länger als das Timeout (7200 Sekunden)
    Wenn der Timeout-Monitor den Job prüft
    Dann sollte ein Event mit Typ "job_timeout" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "timeout_seconds": 7200,
          "job_cancelled": true
        }
        """
      Und das Event sollte "runtime_seconds" enthalten mit Wert > 7200

  Szenario: Job-Cleanup wegen Alter wird protokolliert
    Angenommen ein abgeschlossener Job existiert seit 4000 Sekunden
    Und der TTL ist 3600 Sekunden
    Wenn der Cleanup-Prozess läuft
    Dann sollte ein Event mit Typ "job_cleanup" existieren
      Und die Event-Details sollten enthalten:
        """
        {
          "trigger": "age_exceeded",
          "ttl_seconds": 3600
        }
        """
      Und das Event sollte "age_seconds" enthalten mit Wert > 3600
      Und das Event sollte "files_deleted" enthalten
      Und das Event sollte "total_size_bytes" enthalten

  # =============================================================================
  # Szenario-Gruppe 7: Rückwärtskompatibilität
  # =============================================================================

  Szenario: Alte Jobs ohne events-Feld funktionieren
    Angenommen ein Job wurde vor der Event-Logging-Implementierung erstellt
    Und der Job hat kein "events" Feld in MongoDB
    Wenn der Job über die API abgerufen wird
    Dann sollte der Job erfolgreich geladen werden
    Und job.events sollte eine leere Liste sein
    Und es sollte kein Fehler auftreten

  Szenario: Neue Events können zu alten Jobs hinzugefügt werden
    Angenommen ein alter Job ohne "events" Feld existiert
    Wenn ein neues Event zu diesem Job hinzugefügt wird
    Dann sollte das Event erfolgreich gespeichert werden
    Und job.events sollte das neue Event enthalten
    Und MongoDB sollte das "events" Feld automatisch erstellen

  # =============================================================================
  # Szenario-Gruppe 8: Vollständige Job-Lifecycle-Beispiele
  # =============================================================================

  Szenario: Kompletter Job-Lifecycle für Office-Dokument mit OCR-Skip
    Angenommen eine PowerPoint-Datei "slides.pptx" wird hochgeladen
    Und die Konfiguration ist:
      | Parameter               | Wert     |
      | pdfa_level             | 2        |
      | compression_profile    | balanced |
      | skip_ocr_on_tagged_pdfs| true     |
    Wenn der Konvertierungsjob vollständig ausgeführt wird
    Dann sollten folgende Events in dieser Reihenfolge existieren:
      | Event-Typ             | Erwartete Details                          |
      | format_conversion     | pptx→pdf, office_to_pdf                   |
      | ocr_decision          | skip, tagged_pdf                           |
      | compression_selected  | preserve, auto_switched_for_tagged_pdf     |
    Und alle Events sollten einen Timestamp haben
    Und alle Events sollten eine message haben
    Und die Events sollten chronologisch sortiert sein

  Szenario: Kompletter Job-Lifecycle für gescannte PDF mit Fallback
    Angenommen eine gescannte PDF-Datei "old-scan.pdf" wird hochgeladen
    Und die PDF verursacht Ghostscript-Fehler
    Und die Konfiguration ist:
      | Parameter  | Wert |
      | pdfa_level | 3    |
    Wenn der Konvertierungsjob vollständig ausgeführt wird
    Dann sollten folgende Events existieren:
      | Event-Typ         | Erwartete Details           |
      | format_conversion | pdf→pdf, no conversion      |
      | ocr_decision      | perform, no_text            |
      | fallback_applied  | tier 2, ghostscript_error   |
    Und das fallback_applied Event sollte safe_mode_config enthalten
    Und das fallback_applied Event sollte pdfa_level_downgrade enthalten

  # =============================================================================
  # Szenario-Gruppe 9: Error Handling
  # =============================================================================

  Szenario: Event-Logging-Fehler blockieren Konvertierung nicht
    Angenommen eine PDF-Datei "document.pdf" wird hochgeladen
    Und MongoDB ist vorübergehend nicht erreichbar
    Wenn der Konvertierungsjob ausgeführt wird
    Dann sollte die Konvertierung erfolgreich abgeschlossen werden
    Und der Job-Status sollte "completed" sein
    Aber Events könnten fehlen oder unvollständig sein
    Und ein Warnung sollte im Log erscheinen

  Szenario: Event-Callback ist optional
    Angenommen convert_to_pdfa() wird ohne event_callback aufgerufen
    Wenn die Konvertierung ausgeführt wird
    Dann sollte die Konvertierung erfolgreich sein
    Und es sollten keine Events geloggt werden
    Und es sollte kein Fehler auftreten
