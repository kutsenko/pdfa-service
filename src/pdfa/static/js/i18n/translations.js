/**
 * Internationalization translations for PDF/A Converter
 * Supports: English, German, Spanish, French
 */

export const translations = {
            en: {
                'page.title': 'PDF/A Converter - Test Interface',
                'header.title': '📄 PDF/A Converter',
                'header.subtitle': 'Convert your documents to archival PDF/A format with OCR',
                'info.supportedFormats': 'ℹ️ Supported formats: PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP',
                'form.selectFile': 'Select File',
                'form.uploadText': 'Click to upload or drag and drop',
                'form.uploadSubtext': 'PDF, Office, or OpenDocument files',
                'form.ocrLanguage': 'OCR Language',
                'form.pdfaLevel': 'PDF/A Level',
                'form.compressionProfile': 'Compression Profile',
                'form.enableOcr': 'Enable OCR (text recognition)',
                'form.ocrHint': 'Uncheck to skip OCR and only convert to PDF/A format',
                'form.skipOcrOnTagged': 'Skip OCR for tagged PDFs',
                'form.skipOcrHint': 'PDFs with accessibility tags will preserve their structure without OCR',
                'form.convertButton': '🚀 Convert & Download',
                'form.clearButton': 'Clear',
                'ocr.english': 'English',
                'ocr.german': 'Deutsch (German)',
                'ocr.germanEnglish': 'Deutsch + English',
                'ocr.french': 'Français (French)',
                'ocr.frenchEnglish': 'Français + English',
                'ocr.spanish': 'Español (Spanish)',
                'ocr.spanishEnglish': 'Español + English',
                'ocr.italian': 'Italiano (Italian)',
                'ocr.italianEnglish': 'Italiano + English',
                'compression.balanced': 'Balanced (150 DPI, Quality 85)',
                'compression.quality': 'High Quality (300 DPI, Quality 95)',
                'compression.aggressive': 'Aggressive (100 DPI, Quality 75)',
                'compression.minimal': 'Minimal Size (72 DPI, Quality 70)',
                'status.selectFile': 'Please select a file first',
                'status.fileTooLarge': 'File too large: {size}. Maximum size is {max}.',
                'status.converting': 'Converting... This may take a moment',
                'status.success': '✓ Conversion successful! Your file has been downloaded.',
                'status.viewPdf': '👁️ View PDF',
                'status.error': '✗ Error: {message}',
                'error.badRequest': 'Invalid file or parameters. Please check your file and try again.',
                'error.payloadTooLarge': 'File size exceeds server limit. Please use a smaller file.',
                'error.requestTimeout': 'Request timed out. The server took too long to respond.',
                'error.internalServer': 'Server error occurred. Please try again later.',
                'error.gatewayTimeout': 'Gateway timeout. The conversion is taking longer than expected.',
                'error.networkError': 'Network error. Please check your internet connection.',
                'error.connectionRefused': 'Cannot connect to server. Please try again later.',
                'error.timeout': 'Request timeout. Please try again with a smaller file or later.',
                'error.unknown': 'An unknown error occurred: {message}',
                // WebSocket-specific translations
                'ws.connecting': 'Connecting...',
                'ws.connected': 'Connected',
                'ws.disconnected': 'Disconnected - reconnecting...',
                'ws.reconnected': 'Reconnected',
                'ws.error': 'WebSocket error',
                'progress.office': 'Converting Office document to PDF...',
                'progress.scanning': 'Analyzing PDF structure...',
                'progress.ocr': 'OCR processing: page {current} of {total}',
                'progress.pdfa': 'Converting to PDF/A format...',
                'button.cancel': 'Cancel',
                'status.queued': 'Queued - waiting for processing...',
                'status.processing': 'Processing...',
                'status.cancelling': 'Cancelling...',
                'status.cancelled': 'Conversion cancelled',
                'error.job_timeout': 'Conversion timeout exceeded',
                'error.job_cancelled': 'Job was cancelled',
                'error.ws_connection': 'WebSocket connection failed',
                // Authentication
                'auth.signInTitle': 'Sign in to continue',
                'auth.signInMessage': 'Authentication is required to use the PDF/A converter',
                'auth.signInWithGoogle': 'Sign in with Google',
                'auth.loginFailed': 'Authentication failed. Please try again.',
                'auth.downloadFailed': 'Download failed. Please try again.',
                'auth.viewPdfFailed': 'Failed to open PDF. Please try again.',
                // Welcome screen
                'welcome.title': 'PDF/A Converter',
                'welcome.description': 'Professional document conversion service with OCR support. Convert your PDFs, Office documents, and images to archival PDF/A format - ensuring long-term accessibility and compliance with international standards.',
                'welcome.feature1.title': 'Secure & Private',
                'welcome.feature1.description': 'Your documents are processed securely and never stored permanently',
                'welcome.feature2.title': 'Multi-Language OCR',
                'welcome.feature2.description': 'Support for English, German, French, Spanish, Italian and more',
                'welcome.feature3.title': 'Camera Capture',
                'welcome.feature3.description': 'Scan documents directly with your device camera',
                'welcome.feature4.title': 'Accessibility',
                'welcome.feature4.description': 'Audio guidance and screen reader support for visually impaired users',
                'welcome.cta': 'Please sign in to start converting your documents.',
                // Tab labels
                'tabs.konverter': 'Converter',
                'tabs.kamera': 'Camera',
                'tabs.auftraege': 'Jobs',
                'tabs.konto': 'Account',
                'tabs.dokumentation': 'Documentation',
                // Placeholder content
                'placeholder.kamera.title': 'Camera Scanner',
                'placeholder.kamera.description': 'Coming soon: Upload documents directly from your camera or scanner',
                // Camera Tab translations
                'camera.start': 'Start Camera',
                'camera.stop': 'Stop Camera',
                'camera.capture': 'Capture',
                'camera.switch': 'Switch Camera',
                'camera.selectCamera': 'Select Camera:',
                'camera.pages.title': 'Pages',
                'camera.pages.add': 'Add Page',
                'camera.pages.clear': 'Clear All',
                'camera.pages.submit': 'Convert to PDF/A',
                'camera.settings.title': 'Conversion Settings',
                // Accessibility translations
                'camera.a11y.title': 'Accessibility Assistance',
                'camera.a11y.enable': 'Enable audio guidance',
                'camera.a11y.helpText': 'Provides audio feedback for document edge detection',
                'camera.a11y.volume': 'Volume',
                'camera.a11y.test': 'Test Audio',
                'camera.a11y.testAnnouncement': 'Audio test. If you can hear this, audio is working.',
                'camera.a11y.loading': 'Loading accessibility features...',
                'camera.a11y.statusReady': 'Ready to scan',
                'camera.a11y.edgesDetected': 'Document edges detected. Hold steady.',
                'camera.a11y.edgesLost': 'Edges lost. Adjust camera position.',
                'camera.a11y.topEdge': 'Top edge',
                'camera.a11y.bottomEdge': 'Bottom edge',
                'camera.a11y.leftEdge': 'Left edge',
                'camera.a11y.rightEdge': 'Right edge',
                'camera.a11y.notVisible': 'not visible',
                'camera.a11y.moveCloser': 'Move closer to document',
                'camera.a11y.moveFarther': 'Move farther from document',
                'camera.a11y.enabled': 'Camera assistance enabled',
                'camera.a11y.disabled': 'Camera assistance disabled',
                'camera.a11y.enableAutoCapture': 'Enable automatic capture',
                'camera.a11y.autoCaptureHelp': 'Automatically takes photo after 2 seconds when document is centered',
                'camera.a11y.holdSteady': 'Hold camera steady',
                'camera.a11y.centerDocument': 'Center the document',
                'camera.a11y.photoCaptured': 'Photo captured',
                'camera.edit.rotation': 'Rotation',
                'camera.edit.rotateLeft': '↺ 90° Left',
                'camera.edit.rotateRight': '↻ 90° Right',
                'camera.edit.adjustments': 'Adjustments',
                'camera.edit.brightness': 'Brightness',
                'camera.edit.contrast': 'Contrast',
                'camera.edit.crop': 'Crop',
                'camera.edit.cropButton': '✂️ Crop (Coming Soon)',
                'camera.edit.cropHint': 'Drag on canvas to select area',
                'camera.edit.accept': '✓ Accept',
                'camera.edit.retake': '✗ Retake',
                'camera.errors.noCamera': 'No camera found',
                'camera.errors.permissionDenied': 'Camera permission denied',
                'camera.errors.noPages': 'Please capture at least one page',
                'placeholder.auftraege.title': 'Job History',
                'placeholder.auftraege.description': 'Coming soon: View and manage your conversion history',
                'placeholder.konto.title': 'Account Settings',
                'placeholder.konto.description': 'Coming soon: Manage your account preferences and settings',
                'placeholder.dokumentation.title': 'Documentation',
                'placeholder.dokumentation.description': 'Coming soon: User guides and help documentation',
                // Jobs Tab translations
                'jobs.title': 'Job History',
                'jobs.loading': 'Loading jobs...',
                'jobs.retry': 'Retry',
                'jobs.refresh': 'Refresh',
                'jobs.autoRefresh.on': 'Auto-Refresh: ON',
                'jobs.autoRefresh.off': 'Auto-Refresh: OFF',
                'jobs.filter.all': 'All',
                'jobs.filter.completed': 'Completed',
                'jobs.filter.failed': 'Failed',
                'jobs.filter.processing': 'Processing',
                'jobs.table.status': 'Status',
                'jobs.table.filename': 'Filename',
                'jobs.table.created': 'Created',
                'jobs.table.duration': 'Duration',
                'jobs.table.size': 'Size',
                'jobs.table.events': 'Events',
                'jobs.table.actions': 'Actions',
                'jobs.status.completed': 'Completed',
                'jobs.status.failed': 'Failed',
                'jobs.status.processing': 'Processing',
                'jobs.status.queued': 'Queued',
                'jobs.status.cancelled': 'Cancelled',
                'jobs.actions.download': 'Download',
                'jobs.actions.retry': 'Retry',
                'jobs.actions.expand': 'Expand',
                'jobs.actions.collapse': 'Collapse',
                'jobs.events.empty': 'No events recorded',
                'jobs.download.error': 'Download failed. Please try again.',
                'jobs.retry.notification': 'Please upload {filename} to retry this conversion',
                'jobs.retry.error': 'Failed to load job details. Please try again.',
                'jobs.empty.title': 'No jobs found',
                'jobs.empty.description': 'Start a conversion to see jobs here',
                'jobs.pagination.previous': 'Previous',
                'jobs.pagination.next': 'Next',
                'jobs.pagination.info': '{start}-{end} of {total} jobs',
                'jobs.time.year': '{count} year ago',
                'jobs.time.month': '{count} month ago',
                'jobs.time.week': '{count} week ago',
                'jobs.time.day': '{count} day ago',
                'jobs.time.hour': '{count} hour ago',
                'jobs.time.minute': '{count} minute ago',
                'jobs.time.just_now': 'Just now',
                // Event list translations (flat keys for HTML)
                'events.title': 'Conversion Events',
                'events.details': 'Details',
                // Progress step translations (OCRmyPDF steps)
                progressSteps: {
                    'Starting conversion': 'Starting conversion',
                    'Office conversion': 'Converting Office document',
                    'Scanning contents': 'Scanning contents',
                    'OCR': 'OCR processing',
                    'PDF/A conversion': 'PDF/A conversion',
                    'Linearizing': 'Linearizing',
                    'Recompressing JPEGs': 'Recompressing JPEGs',
                    'Deflating JPEGs': 'Deflating JPEGs',
                    'JBIG2': 'JBIG2 compression',
                    'Optimize': 'Optimizing',
                    'Repair': 'Repairing PDF'
                },
                // Event messages (nested structure for JavaScript)
                events: {
                    messages: {
                        format_conversion: {
                            none: 'No format conversion required (source is PDF)',
                            docx: {
                                success: 'DOCX converted to PDF ({pages} pages)'
                            },
                            xlsx: {
                                success: 'XLSX converted to PDF ({pages} pages)'
                            },
                            pptx: {
                                success: 'PPTX converted to PDF ({pages} slides)'
                            },
                            odt: {
                                success: 'ODT converted to PDF ({pages} pages)'
                            },
                            generic: {
                                success: '{format} converted to PDF'
                            }
                        },
                        ocr_decision: {
                            skip: {
                                tagged_pdf: 'OCR skipped: PDF already tagged',
                                text_detected: 'OCR skipped: searchable text detected',
                                has_text: 'OCR skipped: existing text found',
                                user_request: 'OCR skipped: disabled by user'
                            },
                            perform: {
                                no_text: 'OCR will be performed: no text detected'
                            },
                            apply: {
                                scanned_pdf: 'OCR applied: scanned document detected',
                                low_text_content: 'OCR applied: low text content',
                                user_request: 'OCR applied: forced by user'
                            }
                        },
                        compression_selected: {
                            high: {
                                large_file: 'High compression: file size {size_mb} MB',
                                user_request: 'High compression: requested by user'
                            },
                            balanced: {
                                default: 'Balanced compression: optimal quality/size trade-off'
                            },
                            low: {
                                small_file: 'Low compression: file size {size_mb} MB',
                                user_request: 'Low compression: quality priority'
                            }
                        },
                        passthrough_mode: {
                            valid_pdfa: {
                                pdfa_2b: 'Passthrough: already PDF/A-2b compliant',
                                pdfa_3b: 'Passthrough: already PDF/A-3b compliant'
                            }
                        },
                        fallback_applied: {
                            ocr_failed: {
                                skip_ocr: 'Fallback: OCR failed, proceeding without OCR'
                            },
                            compression_failed: {
                                skip_compression: 'Fallback: compression failed, using original'
                            },
                            conversion_error: {
                                retry_simple: 'Fallback: conversion error, retrying with simplified settings'
                            }
                        },
                        job_timeout: {
                            exceeded: {
                                max_duration: 'Timeout: exceeded maximum duration ({timeout_sec}s)'
                            }
                        },
                        job_cleanup: {
                            success: {
                                temp_files: 'Cleanup: temporary files removed'
                            }
                        }
                    }
                },
                // Modal translations
                modal: {
                    title: 'Conversion Summary',
                    description: 'Your document was successfully converted. Here\'s what happened:',
                    downloadButton: '📥 Download',
                    okButton: 'OK',
                    opened: 'Dialog opened: Conversion Summary'
                },
                // Form labels
                'form.pdfType': 'PDF Type',
                'pdf.standard': 'Standard PDF',
                // Account (Konto) tab
                'konto.loading': 'Loading account information...',
                'konto.error': 'Failed to load account information',
                'konto.retry': 'Retry',
                'konto.accountInfo': 'Account Information',
                'konto.profile': 'Profile',
                'konto.name': 'Name',
                'konto.email': 'Email',
                'konto.userId': 'User ID',
                'konto.loginStats': 'Login Statistics',
                'konto.accountCreated': 'Account Created',
                'konto.lastLogin': 'Last Login',
                'konto.totalLogins': 'Total Logins',
                'konto.jobStats': 'Conversion Statistics',
                'konto.totalJobs': 'Total Jobs',
                'konto.successRate': 'Success Rate',
                'konto.avgDuration': 'Avg Duration',
                'konto.dataProcessed': 'Data Processed',
                'konto.recentActivity': 'Recent Activity',
                'konto.settings': 'Settings',
                'konto.defaultParams': 'Default Conversion Parameters',
                'konto.defaultParamsDesc': 'These settings will be automatically applied when you open the converter.',
                'konto.savePreferences': 'Save Preferences',
                'konto.resetDefaults': 'Reset to Defaults',
                'konto.preferencesSaved': 'Preferences saved successfully',
                'konto.preferencesSaveFailed': 'Failed to save preferences',
                'konto.dangerZone': 'Danger Zone',
                'konto.deleteAccount': 'Delete Account',
                'konto.deleteWarning': '⚠️ This action cannot be undone. This will permanently delete your account, all conversion jobs, activity logs, and preferences.',
                'konto.deleteAccountBtn': 'Delete My Account',
                'konto.deleteDisabled': 'Account deletion is not available in local mode.',
                'konto.confirmDelete': 'Confirm Account Deletion',
                'konto.confirmDeleteDesc': 'To confirm deletion, please type your email address below:',
                'konto.emailMismatch': 'Email does not match',
                'konto.cancel': 'Cancel',
                'konto.confirmDeleteBtn': 'Delete Account',
                'konto.accountDeleted': 'Account deleted successfully. You will be logged out.',
                'konto.deleteFailed': 'Failed to delete account'
            },
            de: {
                'page.title': 'PDF/A Konverter - Testoberfläche',
                'header.title': '📄 PDF/A Konverter',
                'header.subtitle': 'Konvertieren Sie Ihre Dokumente in das archivierbare PDF/A-Format mit OCR',
                'info.supportedFormats': 'ℹ️ Unterstützte Formate: PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP',
                'form.selectFile': 'Datei auswählen',
                'form.uploadText': 'Klicken Sie zum Hochladen oder ziehen Sie die Datei hierher',
                'form.uploadSubtext': 'PDF-, Office- oder OpenDocument-Dateien',
                'form.ocrLanguage': 'OCR-Sprache',
                'form.pdfaLevel': 'PDF/A-Level',
                'form.compressionProfile': 'Komprimierungsprofil',
                'form.enableOcr': 'OCR aktivieren (Texterkennung)',
                'form.ocrHint': 'Deaktivieren, um OCR zu überspringen und nur in PDF/A zu konvertieren',
                'form.skipOcrOnTagged': 'OCR für getaggte PDFs überspringen',
                'form.skipOcrHint': 'PDFs mit Barrierefreiheits-Tags behalten ihre Struktur ohne OCR',
                'form.convertButton': '🚀 Konvertieren & Herunterladen',
                'form.clearButton': 'Löschen',
                'ocr.english': 'Englisch',
                'ocr.german': 'Deutsch',
                'ocr.germanEnglish': 'Deutsch + Englisch',
                'ocr.french': 'Französisch',
                'ocr.frenchEnglish': 'Französisch + Englisch',
                'ocr.spanish': 'Spanisch',
                'ocr.spanishEnglish': 'Spanisch + Englisch',
                'ocr.italian': 'Italienisch',
                'ocr.italianEnglish': 'Italienisch + Englisch',
                'compression.balanced': 'Ausgewogen (150 DPI, Qualität 85)',
                'compression.quality': 'Hohe Qualität (300 DPI, Qualität 95)',
                'compression.aggressive': 'Aggressiv (100 DPI, Qualität 75)',
                'compression.minimal': 'Minimale Größe (72 DPI, Qualität 70)',
                'status.selectFile': 'Bitte wählen Sie zuerst eine Datei aus',
                'status.fileTooLarge': 'Datei zu groß: {size}. Maximale Größe ist {max}.',
                'status.converting': 'Konvertierung läuft... Dies kann einen Moment dauern',
                'status.success': '✓ Konvertierung erfolgreich! Ihre Datei wurde heruntergeladen.',
                'status.viewPdf': '👁️ PDF anzeigen',
                'status.error': '✗ Fehler: {message}',
                'error.badRequest': 'Ungültige Datei oder Parameter. Bitte überprüfen Sie Ihre Datei und versuchen Sie es erneut.',
                'error.payloadTooLarge': 'Dateigröße überschreitet Serverlimit. Bitte verwenden Sie eine kleinere Datei.',
                'error.requestTimeout': 'Zeitüberschreitung der Anfrage. Der Server hat zu lange gebraucht.',
                'error.internalServer': 'Serverfehler aufgetreten. Bitte versuchen Sie es später erneut.',
                'error.gatewayTimeout': 'Gateway-Zeitüberschreitung. Die Konvertierung dauert länger als erwartet.',
                'error.networkError': 'Netzwerkfehler. Bitte überprüfen Sie Ihre Internetverbindung.',
                'error.connectionRefused': 'Verbindung zum Server fehlgeschlagen. Bitte versuchen Sie es später erneut.',
                'error.timeout': 'Zeitüberschreitung. Bitte versuchen Sie es mit einer kleineren Datei oder später erneut.',
                'error.unknown': 'Ein unbekannter Fehler ist aufgetreten: {message}',
                // WebSocket-specific translations
                'ws.connecting': 'Verbindung wird hergestellt...',
                'ws.connected': 'Verbunden',
                'ws.disconnected': 'Verbindung unterbrochen - Wiederverbindung...',
                'ws.reconnected': 'Wiederverbunden',
                'ws.error': 'WebSocket-Fehler',
                'progress.office': 'Office-Dokument wird zu PDF konvertiert...',
                'progress.scanning': 'PDF-Struktur wird analysiert...',
                'progress.ocr': 'OCR-Verarbeitung: Seite {current} von {total}',
                'progress.pdfa': 'Konvertierung zu PDF/A-Format...',
                'button.cancel': 'Abbrechen',
                'status.queued': 'In Warteschlange - warte auf Verarbeitung...',
                'status.processing': 'Verarbeitung läuft...',
                'status.cancelling': 'Wird abgebrochen...',
                'status.cancelled': 'Konvertierung abgebrochen',
                'error.job_timeout': 'Konvertierungs-Timeout überschritten',
                'error.job_cancelled': 'Job wurde abgebrochen',
                'error.ws_connection': 'WebSocket-Verbindung fehlgeschlagen',
                // Authentifizierung
                'auth.signInTitle': 'Anmelden um fortzufahren',
                'auth.signInMessage': 'Authentifizierung ist erforderlich, um den PDF/A-Konverter zu verwenden',
                'auth.signInWithGoogle': 'Mit Google anmelden',
                'auth.loginFailed': 'Authentifizierung fehlgeschlagen. Bitte versuchen Sie es erneut.',
                'auth.downloadFailed': 'Download fehlgeschlagen. Bitte versuchen Sie es erneut.',
                'auth.viewPdfFailed': 'PDF konnte nicht geöffnet werden. Bitte versuchen Sie es erneut.',
                // Willkommensbildschirm
                'welcome.title': 'PDF/A-Konverter',
                'welcome.description': 'Professioneller Dokumentenkonvertierungsdienst mit OCR-Unterstützung. Konvertieren Sie Ihre PDFs, Office-Dokumente und Bilder in das archivfähige PDF/A-Format - für langfristige Zugänglichkeit und Einhaltung internationaler Standards.',
                'welcome.feature1.title': 'Sicher & Privat',
                'welcome.feature1.description': 'Ihre Dokumente werden sicher verarbeitet und niemals dauerhaft gespeichert',
                'welcome.feature2.title': 'Mehrsprachige OCR',
                'welcome.feature2.description': 'Unterstützung für Englisch, Deutsch, Französisch, Spanisch, Italienisch und mehr',
                'welcome.feature3.title': 'Kamera-Erfassung',
                'welcome.feature3.description': 'Scannen Sie Dokumente direkt mit Ihrer Gerätekamera',
                'welcome.feature4.title': 'Barrierefreiheit',
                'welcome.feature4.description': 'Audiounterstützung und Screenreader-Unterstützung für sehbehinderte Benutzer',
                'welcome.cta': 'Bitte melden Sie sich an, um mit der Konvertierung Ihrer Dokumente zu beginnen.',
                // Tab-Beschriftungen
                'tabs.konverter': 'Konverter',
                'tabs.kamera': 'Kamera',
                'tabs.auftraege': 'Aufträge',
                'tabs.konto': 'Konto',
                'tabs.dokumentation': 'Dokumentation',
                // Platzhalter-Inhalte
                'placeholder.kamera.title': 'Kamera-Scanner',
                'placeholder.kamera.description': 'Demnächst: Dokumente direkt von Ihrer Kamera oder Ihrem Scanner hochladen',
                // Kamera-Tab-Übersetzungen
                'camera.start': 'Kamera starten',
                'camera.stop': 'Kamera stoppen',
                'camera.capture': 'Aufnehmen',
                'camera.switch': 'Kamera wechseln',
                'camera.selectCamera': 'Kamera auswählen:',
                'camera.pages.title': 'Seiten',
                'camera.pages.add': 'Seite hinzufügen',
                'camera.pages.clear': 'Alle löschen',
                'camera.pages.submit': 'In PDF/A konvertieren',
                'camera.settings.title': 'Konvertierungseinstellungen',
                // Barrierefreiheits-Übersetzungen
                'camera.a11y.title': 'Barrierefreiheits-Unterstützung',
                'camera.a11y.enable': 'Audio-Führung aktivieren',
                'camera.a11y.helpText': 'Bietet akustisches Feedback zur Dokumentenerkennung',
                'camera.a11y.volume': 'Lautstärke',
                'camera.a11y.test': 'Audio testen',
                'camera.a11y.testAnnouncement': 'Audiotest. Wenn Sie dies hören können, funktioniert Audio.',
                'camera.a11y.loading': 'Lade Barrierefreiheits-Funktionen...',
                'camera.a11y.statusReady': 'Bereit zum Scannen',
                'camera.a11y.edgesDetected': 'Dokumentränder erkannt. Halten Sie ruhig.',
                'camera.a11y.edgesLost': 'Ränder verloren. Kameraposition anpassen.',
                'camera.a11y.topEdge': 'Oberer Rand',
                'camera.a11y.bottomEdge': 'Unterer Rand',
                'camera.a11y.leftEdge': 'Linker Rand',
                'camera.a11y.rightEdge': 'Rechter Rand',
                'camera.a11y.notVisible': 'nicht sichtbar',
                'camera.a11y.moveCloser': 'Näher ans Dokument',
                'camera.a11y.moveFarther': 'Weiter weg vom Dokument',
                'camera.a11y.enabled': 'Kamera-Unterstützung aktiviert',
                'camera.a11y.disabled': 'Kamera-Unterstützung deaktiviert',
                'camera.a11y.enableAutoCapture': 'Automatische Aufnahme aktivieren',
                'camera.a11y.autoCaptureHelp': 'Nimmt automatisch ein Foto nach 2 Sekunden auf, wenn das Dokument zentriert ist',
                'camera.a11y.holdSteady': 'Kamera ruhig halten',
                'camera.a11y.centerDocument': 'Dokument zentrieren',
                'camera.a11y.photoCaptured': 'Foto aufgenommen',
                'camera.edit.rotation': 'Drehung',
                'camera.edit.rotateLeft': '↺ 90° Links',
                'camera.edit.rotateRight': '↻ 90° Rechts',
                'camera.edit.adjustments': 'Anpassungen',
                'camera.edit.brightness': 'Helligkeit',
                'camera.edit.contrast': 'Kontrast',
                'camera.edit.crop': 'Zuschneiden',
                'camera.edit.cropButton': '✂️ Zuschneiden (Demnächst)',
                'camera.edit.cropHint': 'Ziehen Sie auf der Leinwand, um einen Bereich auszuwählen',
                'camera.edit.accept': '✓ Übernehmen',
                'camera.edit.retake': '✗ Erneut aufnehmen',
                'camera.errors.noCamera': 'Keine Kamera gefunden',
                'camera.errors.permissionDenied': 'Kamera-Berechtigung verweigert',
                'camera.errors.noPages': 'Bitte mindestens eine Seite aufnehmen',
                'placeholder.auftraege.title': 'Auftragsverlauf',
                'placeholder.auftraege.description': 'Demnächst: Ihren Konvertierungsverlauf anzeigen und verwalten',
                'placeholder.konto.title': 'Kontoeinstellungen',
                'placeholder.konto.description': 'Demnächst: Ihre Kontoeinstellungen und Präferenzen verwalten',
                'placeholder.dokumentation.title': 'Dokumentation',
                'placeholder.dokumentation.description': 'Demnächst: Benutzerhandbücher und Hilfedokumentation',
                // Aufträge-Tab-Übersetzungen
                'jobs.title': 'Aufträge',
                'jobs.loading': 'Lade Aufträge...',
                'jobs.retry': 'Wiederholen',
                'jobs.refresh': 'Aktualisieren',
                'jobs.autoRefresh.on': 'Auto-Aktualisierung: EIN',
                'jobs.autoRefresh.off': 'Auto-Aktualisierung: AUS',
                'jobs.filter.all': 'Alle',
                'jobs.filter.completed': 'Abgeschlossen',
                'jobs.filter.failed': 'Fehlgeschlagen',
                'jobs.filter.processing': 'In Bearbeitung',
                'jobs.table.status': 'Status',
                'jobs.table.filename': 'Dateiname',
                'jobs.table.created': 'Erstellt',
                'jobs.table.duration': 'Dauer',
                'jobs.table.size': 'Größe',
                'jobs.table.events': 'Ereignisse',
                'jobs.table.actions': 'Aktionen',
                'jobs.status.completed': 'Abgeschlossen',
                'jobs.status.failed': 'Fehlgeschlagen',
                'jobs.status.processing': 'In Bearbeitung',
                'jobs.status.queued': 'Warteschlange',
                'jobs.status.cancelled': 'Abgebrochen',
                'jobs.actions.download': 'Herunterladen',
                'jobs.actions.retry': 'Wiederholen',
                'jobs.actions.expand': 'Erweitern',
                'jobs.actions.collapse': 'Einklappen',
                'jobs.events.empty': 'Keine Ereignisse aufgezeichnet',
                'jobs.download.error': 'Download fehlgeschlagen. Bitte erneut versuchen.',
                'jobs.retry.notification': 'Bitte laden Sie {filename} hoch, um diese Konvertierung zu wiederholen',
                'jobs.retry.error': 'Fehler beim Laden der Auftragsdetails. Bitte erneut versuchen.',
                'jobs.empty.title': 'Keine Aufträge gefunden',
                'jobs.empty.description': 'Starten Sie eine Konvertierung, um Aufträge hier zu sehen',
                'jobs.pagination.previous': 'Zurück',
                'jobs.pagination.next': 'Weiter',
                'jobs.pagination.info': '{start}-{end} von {total} Aufträgen',
                'jobs.time.year': 'vor {count} Jahr',
                'jobs.time.month': 'vor {count} Monat',
                'jobs.time.week': 'vor {count} Woche',
                'jobs.time.day': 'vor {count} Tag',
                'jobs.time.hour': 'vor {count} Stunde',
                'jobs.time.minute': 'vor {count} Minute',
                'jobs.time.just_now': 'Gerade eben',
                // Event-Listen-Übersetzungen (flache Schlüssel für HTML)
                'events.title': 'Konvertierungsereignisse',
                'events.details': 'Details',
                // Fortschrittsschritt-Übersetzungen (OCRmyPDF-Schritte)
                progressSteps: {
                    'Starting conversion': 'Konvertierung wird gestartet',
                    'Office conversion': 'Office-Dokument wird konvertiert',
                    'Scanning contents': 'Inhalt wird gescannt',
                    'OCR': 'OCR-Verarbeitung',
                    'PDF/A conversion': 'PDF/A-Konvertierung',
                    'Linearizing': 'Linearisierung',
                    'Recompressing JPEGs': 'JPEGs werden neu komprimiert',
                    'Deflating JPEGs': 'JPEGs werden entpackt',
                    'JBIG2': 'JBIG2-Komprimierung',
                    'Optimize': 'Optimierung',
                    'Repair': 'PDF wird repariert'
                },
                // Event-Nachrichten (verschachtelte Struktur für JavaScript)
                events: {
                    messages: {
                        format_conversion: {
                            none: 'Keine Formatkonvertierung erforderlich (Quelle ist PDF)',
                            docx: {
                                success: 'DOCX in PDF konvertiert ({pages} Seiten)'
                            },
                            xlsx: {
                                success: 'XLSX in PDF konvertiert ({pages} Seiten)'
                            },
                            pptx: {
                                success: 'PPTX in PDF konvertiert ({pages} Folien)'
                            },
                            odt: {
                                success: 'ODT in PDF konvertiert ({pages} Seiten)'
                            },
                            generic: {
                                success: '{format} in PDF konvertiert'
                            }
                        },
                        ocr_decision: {
                            skip: {
                                tagged_pdf: 'OCR übersprungen: PDF bereits getaggt',
                                text_detected: 'OCR übersprungen: durchsuchbarer Text erkannt',
                                has_text: 'OCR übersprungen: vorhandener Text gefunden',
                                user_request: 'OCR übersprungen: vom Benutzer deaktiviert'
                            },
                            perform: {
                                no_text: 'OCR wird durchgeführt: kein Text erkannt'
                            },
                            apply: {
                                scanned_pdf: 'OCR angewandt: gescanntes Dokument erkannt',
                                low_text_content: 'OCR angewandt: wenig Textinhalt',
                                user_request: 'OCR angewandt: vom Benutzer erzwungen'
                            }
                        },
                        compression_selected: {
                            high: {
                                large_file: 'Hohe Komprimierung: Dateigröße {size_mb} MB',
                                user_request: 'Hohe Komprimierung: vom Benutzer angefordert'
                            },
                            balanced: {
                                default: 'Ausgewogene Komprimierung: optimaler Qualität/Größe-Kompromiss'
                            },
                            low: {
                                small_file: 'Niedrige Komprimierung: Dateigröße {size_mb} MB',
                                user_request: 'Niedrige Komprimierung: Qualität priorisiert'
                            }
                        },
                        passthrough_mode: {
                            valid_pdfa: {
                                pdfa_2b: 'Passthrough: bereits PDF/A-2b-konform',
                                pdfa_3b: 'Passthrough: bereits PDF/A-3b-konform'
                            }
                        },
                        fallback_applied: {
                            ocr_failed: {
                                skip_ocr: 'Fallback: OCR fehlgeschlagen, fortfahren ohne OCR'
                            },
                            compression_failed: {
                                skip_compression: 'Fallback: Komprimierung fehlgeschlagen, Original verwenden'
                            },
                            conversion_error: {
                                retry_simple: 'Fallback: Konvertierungsfehler, Wiederholung mit vereinfachten Einstellungen'
                            }
                        },
                        job_timeout: {
                            exceeded: {
                                max_duration: 'Timeout: maximale Dauer überschritten ({timeout_sec}s)'
                            }
                        },
                        job_cleanup: {
                            success: {
                                temp_files: 'Aufräumen: temporäre Dateien entfernt'
                            }
                        }
                    }
                },
                // Modal-Übersetzungen
                modal: {
                    title: 'Konvertierungs-Zusammenfassung',
                    description: 'Ihr Dokument wurde erfolgreich konvertiert. Das ist passiert:',
                    downloadButton: '📥 Herunterladen',
                    okButton: 'OK',
                    opened: 'Dialog geöffnet: Konvertierungs-Zusammenfassung'
                },
                // Formular-Labels
                'form.pdfType': 'PDF-Typ',
                'pdf.standard': 'Standard-PDF',
                // Konto-Tab
                'konto.loading': 'Lade Konto-Informationen...',
                'konto.error': 'Fehler beim Laden der Konto-Informationen',
                'konto.retry': 'Erneut versuchen',
                'konto.accountInfo': 'Konto-Informationen',
                'konto.profile': 'Profil',
                'konto.name': 'Name',
                'konto.email': 'E-Mail',
                'konto.userId': 'Benutzer-ID',
                'konto.loginStats': 'Login-Statistiken',
                'konto.accountCreated': 'Konto erstellt',
                'konto.lastLogin': 'Letzter Login',
                'konto.totalLogins': 'Gesamte Logins',
                'konto.jobStats': 'Konvertierungsstatistiken',
                'konto.totalJobs': 'Gesamte Jobs',
                'konto.successRate': 'Erfolgsrate',
                'konto.avgDuration': 'Durchschn. Dauer',
                'konto.dataProcessed': 'Verarbeitete Daten',
                'konto.recentActivity': 'Letzte Aktivitäten',
                'konto.settings': 'Einstellungen',
                'konto.defaultParams': 'Standard-Konvertierungsparameter',
                'konto.defaultParamsDesc': 'Diese Einstellungen werden automatisch angewendet, wenn Sie den Konverter öffnen.',
                'konto.savePreferences': 'Einstellungen speichern',
                'konto.resetDefaults': 'Auf Standard zurücksetzen',
                'konto.preferencesSaved': 'Einstellungen erfolgreich gespeichert',
                'konto.preferencesSaveFailed': 'Fehler beim Speichern der Einstellungen',
                'konto.dangerZone': 'Gefahrenbereich',
                'konto.deleteAccount': 'Konto löschen',
                'konto.deleteWarning': '⚠️ Diese Aktion kann nicht rückgängig gemacht werden. Ihr Konto, alle Konvertierungsjobs, Aktivitätsprotokolle und Einstellungen werden dauerhaft gelöscht.',
                'konto.deleteAccountBtn': 'Mein Konto löschen',
                'konto.deleteDisabled': 'Konto-Löschung ist im lokalen Modus nicht verfügbar.',
                'konto.confirmDelete': 'Konto-Löschung bestätigen',
                'konto.confirmDeleteDesc': 'Zur Bestätigung geben Sie bitte Ihre E-Mail-Adresse ein:',
                'konto.emailMismatch': 'E-Mail stimmt nicht überein',
                'konto.cancel': 'Abbrechen',
                'konto.confirmDeleteBtn': 'Konto löschen',
                'konto.accountDeleted': 'Konto erfolgreich gelöscht. Sie werden abgemeldet.',
                'konto.deleteFailed': 'Fehler beim Löschen des Kontos'
            },
            es: {
                'page.title': 'Convertidor PDF/A - Interfaz de Prueba',
                'header.title': '📄 Convertidor PDF/A',
                'header.subtitle': 'Convierta sus documentos al formato archivístico PDF/A con OCR',
                'info.supportedFormats': 'ℹ️ Formatos compatibles: PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP',
                'form.selectFile': 'Seleccionar archivo',
                'form.uploadText': 'Haga clic para cargar o arrastre y suelte',
                'form.uploadSubtext': 'Archivos PDF, Office u OpenDocument',
                'form.ocrLanguage': 'Idioma OCR',
                'form.pdfaLevel': 'Nivel PDF/A',
                'form.compressionProfile': 'Perfil de Compresión',
                'form.enableOcr': 'Activar OCR (reconocimiento de texto)',
                'form.ocrHint': 'Desmarque para omitir OCR y solo convertir a formato PDF/A',
                'form.skipOcrOnTagged': 'Omitir OCR para PDFs etiquetados',
                'form.skipOcrHint': 'Los PDFs con etiquetas de accesibilidad conservarán su estructura sin OCR',
                'form.convertButton': '🚀 Convertir y Descargar',
                'form.clearButton': 'Limpiar',
                'ocr.english': 'Inglés',
                'ocr.german': 'Alemán',
                'ocr.germanEnglish': 'Alemán + Inglés',
                'ocr.french': 'Francés',
                'ocr.frenchEnglish': 'Francés + Inglés',
                'ocr.spanish': 'Español',
                'ocr.spanishEnglish': 'Español + Inglés',
                'ocr.italian': 'Italiano',
                'ocr.italianEnglish': 'Italiano + Inglés',
                'compression.balanced': 'Equilibrado (150 DPI, Calidad 85)',
                'compression.quality': 'Alta Calidad (300 DPI, Calidad 95)',
                'compression.aggressive': 'Agresivo (100 DPI, Calidad 75)',
                'compression.minimal': 'Tamaño Mínimo (72 DPI, Calidad 70)',
                'status.selectFile': 'Por favor, seleccione primero un archivo',
                'status.fileTooLarge': 'Archivo demasiado grande: {size}. El tamaño máximo es {max}.',
                'status.converting': 'Convirtiendo... Esto puede tardar un momento',
                'status.success': '✓ ¡Conversión exitosa! Su archivo ha sido descargado.',
                'status.viewPdf': '👁️ Ver PDF',
                'status.error': '✗ Error: {message}',
                'error.badRequest': 'Archivo o parámetros inválidos. Por favor, verifique su archivo e inténtelo de nuevo.',
                'error.payloadTooLarge': 'El tamaño del archivo excede el límite del servidor. Por favor, use un archivo más pequeño.',
                'error.requestTimeout': 'Se agotó el tiempo de espera de la solicitud. El servidor tardó demasiado en responder.',
                'error.internalServer': 'Ocurrió un error en el servidor. Por favor, inténtelo de nuevo más tarde.',
                'error.gatewayTimeout': 'Tiempo de espera agotado. La conversión está tardando más de lo esperado.',
                'error.networkError': 'Error de red. Por favor, verifique su conexión a internet.',
                'error.connectionRefused': 'No se puede conectar al servidor. Por favor, inténtelo de nuevo más tarde.',
                'error.timeout': 'Tiempo de espera agotado. Por favor, inténtelo con un archivo más pequeño o más tarde.',
                'error.unknown': 'Ocurrió un error desconocido: {message}',
                // WebSocket-specific translations
                'ws.connecting': 'Conectando...',
                'ws.connected': 'Conectado',
                'ws.disconnected': 'Desconectado - reconectando...',
                'ws.reconnected': 'Reconectado',
                'ws.error': 'Error de WebSocket',
                'progress.office': 'Convirtiendo documento Office a PDF...',
                'progress.scanning': 'Analizando estructura del PDF...',
                'progress.ocr': 'Procesamiento OCR: página {current} de {total}',
                'progress.pdfa': 'Convirtiendo a formato PDF/A...',
                'button.cancel': 'Cancelar',
                'status.queued': 'En cola - esperando procesamiento...',
                'status.processing': 'Procesando...',
                'status.cancelling': 'Cancelando...',
                'status.cancelled': 'Conversión cancelada',
                'error.job_timeout': 'Tiempo de conversión excedido',
                'error.job_cancelled': 'El trabajo fue cancelado',
                'error.ws_connection': 'Falló la conexión WebSocket',
                // Auth-related translations
                'auth.signInTitle': 'Iniciar sesión para continuar',
                'auth.signInMessage': 'Se requiere autenticación para usar el convertidor PDF/A',
                'auth.signInWithGoogle': 'Iniciar sesión con Google',
                'auth.loginFailed': 'Error de autenticación. Por favor, inténtelo de nuevo.',
                'auth.downloadFailed': 'Error en la descarga. Por favor, inténtelo de nuevo.',
                'auth.viewPdfFailed': 'No se pudo abrir el PDF. Por favor, inténtelo de nuevo.',
                // Pantalla de bienvenida
                'welcome.title': 'Convertidor PDF/A',
                'welcome.description': 'Servicio profesional de conversión de documentos con soporte OCR. Convierta sus PDFs, documentos de Office e imágenes al formato archivístico PDF/A, garantizando la accesibilidad a largo plazo y el cumplimiento de estándares internacionales.',
                'welcome.feature1.title': 'Seguro y Privado',
                'welcome.feature1.description': 'Sus documentos se procesan de forma segura y nunca se almacenan permanentemente',
                'welcome.feature2.title': 'OCR Multiidioma',
                'welcome.feature2.description': 'Soporte para inglés, alemán, francés, español, italiano y más',
                'welcome.feature3.title': 'Captura con Cámara',
                'welcome.feature3.description': 'Escanee documentos directamente con la cámara de su dispositivo',
                'welcome.feature4.title': 'Accesibilidad',
                'welcome.feature4.description': 'Guía por audio y soporte para lectores de pantalla para usuarios con discapacidad visual',
                'welcome.cta': 'Por favor, inicie sesión para comenzar a convertir sus documentos.',
                // Etiquetas de pestañas
                'tabs.konverter': 'Convertidor',
                'tabs.kamera': 'Cámara',
                'tabs.auftraege': 'Trabajos',
                'tabs.konto': 'Cuenta',
                'tabs.dokumentation': 'Documentación',
                // Contenido de marcador de posición
                'placeholder.kamera.title': 'Escáner de Cámara',
                'placeholder.kamera.description': 'Próximamente: Cargue documentos directamente desde su cámara o escáner',
                // Traducciones de la pestaña Cámara
                'camera.start': 'Iniciar Cámara',
                'camera.stop': 'Detener Cámara',
                'camera.capture': 'Capturar',
                'camera.switch': 'Cambiar Cámara',
                'camera.selectCamera': 'Seleccionar Cámara:',
                'camera.pages.title': 'Páginas',
                'camera.pages.add': 'Añadir Página',
                'camera.pages.clear': 'Borrar Todo',
                'camera.pages.submit': 'Convertir a PDF/A',
                'camera.settings.title': 'Configuración de Conversión',
                // Traducciones de accesibilidad
                'camera.a11y.title': 'Asistencia de Accesibilidad',
                'camera.a11y.enable': 'Activar guía de audio',
                'camera.a11y.helpText': 'Proporciona retroalimentación de audio para detección de bordes',
                'camera.a11y.volume': 'Volumen',
                'camera.a11y.test': 'Probar Audio',
                'camera.a11y.testAnnouncement': 'Prueba de audio. Si puede oír esto, el audio funciona.',
                'camera.a11y.loading': 'Cargando funciones de accesibilidad...',
                'camera.a11y.statusReady': 'Listo para escanear',
                'camera.a11y.edgesDetected': 'Bordes del documento detectados. Mantenga firme.',
                'camera.a11y.edgesLost': 'Bordes perdidos. Ajuste la posición de la cámara.',
                'camera.a11y.topEdge': 'Borde superior',
                'camera.a11y.bottomEdge': 'Borde inferior',
                'camera.a11y.leftEdge': 'Borde izquierdo',
                'camera.a11y.rightEdge': 'Borde derecho',
                'camera.a11y.notVisible': 'no visible',
                'camera.a11y.moveCloser': 'Acérquese al documento',
                'camera.a11y.moveFarther': 'Aléjese del documento',
                'camera.a11y.enabled': 'Asistencia de cámara activada',
                'camera.a11y.disabled': 'Asistencia de cámara desactivada',
                'camera.a11y.enableAutoCapture': 'Activar captura automática',
                'camera.a11y.autoCaptureHelp': 'Toma una foto automáticamente después de 2 segundos cuando el documento está centrado',
                'camera.a11y.holdSteady': 'Mantenga la cámara firme',
                'camera.a11y.centerDocument': 'Centre el documento',
                'camera.a11y.photoCaptured': 'Foto capturada',
                'camera.edit.rotation': 'Rotación',
                'camera.edit.rotateLeft': '↺ 90° Izquierda',
                'camera.edit.rotateRight': '↻ 90° Derecha',
                'camera.edit.adjustments': 'Ajustes',
                'camera.edit.brightness': 'Brillo',
                'camera.edit.contrast': 'Contraste',
                'camera.edit.crop': 'Recortar',
                'camera.edit.cropButton': '✂️ Recortar (Próximamente)',
                'camera.edit.cropHint': 'Arrastre en el lienzo para seleccionar área',
                'camera.edit.accept': '✓ Aceptar',
                'camera.edit.retake': '✗ Volver a Tomar',
                'camera.errors.noCamera': 'No se encontró cámara',
                'camera.errors.permissionDenied': 'Permiso de cámara denegado',
                'camera.errors.noPages': 'Por favor, capture al menos una página',
                'placeholder.auftraege.title': 'Historial de Trabajos',
                'placeholder.auftraege.description': 'Próximamente: Vea y administre su historial de conversiones',
                'placeholder.konto.title': 'Configuración de Cuenta',
                'placeholder.konto.description': 'Próximamente: Administre sus preferencias y configuraciones de cuenta',
                'placeholder.dokumentation.title': 'Documentación',
                'placeholder.dokumentation.description': 'Próximamente: Guías de usuario y documentación de ayuda',
                // Traducciones de la pestaña Trabajos
                'jobs.title': 'Historial de Trabajos',
                'jobs.loading': 'Cargando trabajos...',
                'jobs.retry': 'Reintentar',
                'jobs.refresh': 'Actualizar',
                'jobs.autoRefresh.on': 'Actualización Automática: ACTIVADA',
                'jobs.autoRefresh.off': 'Actualización Automática: DESACTIVADA',
                'jobs.filter.all': 'Todos',
                'jobs.filter.completed': 'Completados',
                'jobs.filter.failed': 'Fallidos',
                'jobs.filter.processing': 'Procesando',
                'jobs.table.status': 'Estado',
                'jobs.table.filename': 'Nombre de Archivo',
                'jobs.table.created': 'Creado',
                'jobs.table.duration': 'Duración',
                'jobs.table.size': 'Tamaño',
                'jobs.table.events': 'Eventos',
                'jobs.table.actions': 'Acciones',
                'jobs.status.completed': 'Completado',
                'jobs.status.failed': 'Fallido',
                'jobs.status.processing': 'Procesando',
                'jobs.status.queued': 'En Cola',
                'jobs.status.cancelled': 'Cancelado',
                'jobs.actions.download': 'Descargar',
                'jobs.actions.retry': 'Reintentar',
                'jobs.actions.expand': 'Expandir',
                'jobs.actions.collapse': 'Contraer',
                'jobs.events.empty': 'No hay eventos registrados',
                'jobs.download.error': 'Error al descargar. Inténtelo de nuevo.',
                'jobs.retry.notification': 'Por favor suba {filename} para reintentar esta conversión',
                'jobs.retry.error': 'Error al cargar los detalles del trabajo. Inténtelo de nuevo.',
                'jobs.empty.title': 'No se encontraron trabajos',
                'jobs.empty.description': 'Inicie una conversión para ver trabajos aquí',
                'jobs.pagination.previous': 'Anterior',
                'jobs.pagination.next': 'Siguiente',
                'jobs.pagination.info': '{start}-{end} de {total} trabajos',
                'jobs.time.year': 'hace {count} año',
                'jobs.time.month': 'hace {count} mes',
                'jobs.time.week': 'hace {count} semana',
                'jobs.time.day': 'hace {count} día',
                'jobs.time.hour': 'hace {count} hora',
                'jobs.time.minute': 'hace {count} minuto',
                'jobs.time.just_now': 'Justo ahora',
                // Traducciones de lista de eventos (claves planas para HTML)
                'events.title': 'Eventos de Conversión',
                'events.details': 'Detalles',
                // Traducciones de pasos de progreso (pasos de OCRmyPDF)
                progressSteps: {
                    'Starting conversion': 'Iniciando conversión',
                    'Office conversion': 'Convirtiendo documento Office',
                    'Scanning contents': 'Escaneando contenido',
                    'OCR': 'Procesamiento OCR',
                    'PDF/A conversion': 'Conversión a PDF/A',
                    'Linearizing': 'Linearización',
                    'Recompressing JPEGs': 'Recomprimiendo JPEGs',
                    'Deflating JPEGs': 'Descomprimiendo JPEGs',
                    'JBIG2': 'Compresión JBIG2',
                    'Optimize': 'Optimización',
                    'Repair': 'Reparando PDF'
                },
                // Mensajes de eventos (estructura anidada para JavaScript)
                events: {
                    messages: {
                        format_conversion: {
                            none: 'No se requiere conversión de formato (la fuente es PDF)',
                            docx: {
                                success: 'DOCX convertido a PDF ({pages} páginas)'
                            },
                            xlsx: {
                                success: 'XLSX convertido a PDF ({pages} páginas)'
                            },
                            pptx: {
                                success: 'PPTX convertido a PDF ({pages} diapositivas)'
                            },
                            odt: {
                                success: 'ODT convertido a PDF ({pages} páginas)'
                            },
                            generic: {
                                success: '{format} convertido a PDF'
                            }
                        },
                        ocr_decision: {
                            skip: {
                                tagged_pdf: 'OCR omitido: PDF ya etiquetado',
                                text_detected: 'OCR omitido: texto buscable detectado',
                                has_text: 'OCR omitido: texto existente encontrado',
                                user_request: 'OCR omitido: deshabilitado por el usuario'
                            },
                            perform: {
                                no_text: 'Se realizará OCR: no se detectó texto'
                            },
                            apply: {
                                scanned_pdf: 'OCR aplicado: documento escaneado detectado',
                                low_text_content: 'OCR aplicado: bajo contenido de texto',
                                user_request: 'OCR aplicado: forzado por el usuario'
                            }
                        },
                        compression_selected: {
                            high: {
                                large_file: 'Compresión alta: tamaño de archivo {size_mb} MB',
                                user_request: 'Compresión alta: solicitada por el usuario'
                            },
                            balanced: {
                                default: 'Compresión equilibrada: compensación óptima calidad/tamaño'
                            },
                            low: {
                                small_file: 'Compresión baja: tamaño de archivo {size_mb} MB',
                                user_request: 'Compresión baja: prioridad de calidad'
                            }
                        },
                        passthrough_mode: {
                            valid_pdfa: {
                                pdfa_2b: 'Passthrough: ya cumple con PDF/A-2b',
                                pdfa_3b: 'Passthrough: ya cumple con PDF/A-3b'
                            }
                        },
                        fallback_applied: {
                            ocr_failed: {
                                skip_ocr: 'Fallback: OCR falló, continuando sin OCR'
                            },
                            compression_failed: {
                                skip_compression: 'Fallback: compresión falló, usando original'
                            },
                            conversion_error: {
                                retry_simple: 'Fallback: error de conversión, reintentando con configuración simplificada'
                            }
                        },
                        job_timeout: {
                            exceeded: {
                                max_duration: 'Tiempo de espera: duración máxima excedida ({timeout_sec}s)'
                            }
                        },
                        job_cleanup: {
                            success: {
                                temp_files: 'Limpieza: archivos temporales eliminados'
                            }
                        }
                    }
                },
                // Traducciones del modal
                modal: {
                    title: 'Resumen de Conversión',
                    description: 'Su documento se convirtió exitosamente. Esto es lo que sucedió:',
                    downloadButton: '📥 Descargar',
                    okButton: 'OK',
                    opened: 'Diálogo abierto: Resumen de Conversión'
                },
                // Etiquetas de formulario
                'form.pdfType': 'Tipo de PDF',
                'pdf.standard': 'PDF Estándar',
                // Pestaña Cuenta (Konto)
                'konto.loading': 'Cargando información de cuenta...',
                'konto.error': 'Error al cargar información de cuenta',
                'konto.retry': 'Reintentar',
                'konto.accountInfo': 'Información de Cuenta',
                'konto.profile': 'Perfil',
                'konto.name': 'Nombre',
                'konto.email': 'Correo',
                'konto.userId': 'ID de Usuario',
                'konto.loginStats': 'Estadísticas de Inicio de Sesión',
                'konto.accountCreated': 'Cuenta Creada',
                'konto.lastLogin': 'Último Inicio de Sesión',
                'konto.totalLogins': 'Total de Inicios',
                'konto.jobStats': 'Estadísticas de Conversión',
                'konto.totalJobs': 'Total de Trabajos',
                'konto.successRate': 'Tasa de Éxito',
                'konto.avgDuration': 'Duración Promedio',
                'konto.dataProcessed': 'Datos Procesados',
                'konto.recentActivity': 'Actividad Reciente',
                'konto.settings': 'Configuración',
                'konto.defaultParams': 'Parámetros de Conversión Predeterminados',
                'konto.defaultParamsDesc': 'Estas configuraciones se aplicarán automáticamente al abrir el convertidor.',
                'konto.savePreferences': 'Guardar Preferencias',
                'konto.resetDefaults': 'Restablecer Predeterminados',
                'konto.preferencesSaved': 'Preferencias guardadas exitosamente',
                'konto.preferencesSaveFailed': 'Error al guardar preferencias',
                'konto.dangerZone': 'Zona de Peligro',
                'konto.deleteAccount': 'Eliminar Cuenta',
                'konto.deleteWarning': '⚠️ Esta acción no se puede deshacer. Eliminará permanentemente su cuenta, todos los trabajos de conversión, registros de actividad y preferencias.',
                'konto.deleteAccountBtn': 'Eliminar Mi Cuenta',
                'konto.deleteDisabled': 'La eliminación de cuenta no está disponible en modo local.',
                'konto.confirmDelete': 'Confirmar Eliminación de Cuenta',
                'konto.confirmDeleteDesc': 'Para confirmar la eliminación, escriba su dirección de correo electrónico:',
                'konto.emailMismatch': 'El correo no coincide',
                'konto.cancel': 'Cancelar',
                'konto.confirmDeleteBtn': 'Eliminar Cuenta',
                'konto.accountDeleted': 'Cuenta eliminada exitosamente. Será desconectado.',
                'konto.deleteFailed': 'Error al eliminar cuenta'
            },
            fr: {
                'page.title': 'Convertisseur PDF/A - Interface de Test',
                'header.title': '📄 Convertisseur PDF/A',
                'header.subtitle': 'Convertissez vos documents au format archivistique PDF/A avec OCR',
                'info.supportedFormats': 'ℹ️ Formats pris en charge : PDF, DOCX, PPTX, XLSX, ODT, ODS, ODP',
                'form.selectFile': 'Sélectionner un fichier',
                'form.uploadText': 'Cliquez pour télécharger ou glissez-déposez',
                'form.uploadSubtext': 'Fichiers PDF, Office ou OpenDocument',
                'form.ocrLanguage': 'Langue OCR',
                'form.pdfaLevel': 'Niveau PDF/A',
                'form.compressionProfile': 'Profil de Compression',
                'form.enableOcr': 'Activer OCR (reconnaissance de texte)',
                'form.ocrHint': 'Décochez pour ignorer l\'OCR et convertir uniquement au format PDF/A',
                'form.skipOcrOnTagged': 'Ignorer l\'OCR pour les PDFs balisés',
                'form.skipOcrHint': 'Les PDFs avec balises d\'accessibilité conserveront leur structure sans OCR',
                'form.convertButton': '🚀 Convertir et Télécharger',
                'form.clearButton': 'Effacer',
                'ocr.english': 'Anglais',
                'ocr.german': 'Allemand',
                'ocr.germanEnglish': 'Allemand + Anglais',
                'ocr.french': 'Français',
                'ocr.frenchEnglish': 'Français + Anglais',
                'ocr.spanish': 'Espagnol',
                'ocr.spanishEnglish': 'Espagnol + Anglais',
                'ocr.italian': 'Italien',
                'ocr.italianEnglish': 'Italien + Anglais',
                'compression.balanced': 'Équilibré (150 DPI, Qualité 85)',
                'compression.quality': 'Haute Qualité (300 DPI, Qualité 95)',
                'compression.aggressive': 'Agressif (100 DPI, Qualité 75)',
                'compression.minimal': 'Taille Minimale (72 DPI, Qualité 70)',
                'status.selectFile': 'Veuillez d\'abord sélectionner un fichier',
                'status.fileTooLarge': 'Fichier trop volumineux : {size}. La taille maximale est {max}.',
                'status.converting': 'Conversion en cours... Cela peut prendre un moment',
                'status.success': '✓ Conversion réussie ! Votre fichier a été téléchargé.',
                'status.viewPdf': '👁️ Voir le PDF',
                'status.error': '✗ Erreur : {message}',
                'error.badRequest': 'Fichier ou paramètres invalides. Veuillez vérifier votre fichier et réessayer.',
                'error.payloadTooLarge': 'La taille du fichier dépasse la limite du serveur. Veuillez utiliser un fichier plus petit.',
                'error.requestTimeout': 'Délai d\'attente de la demande expiré. Le serveur a mis trop de temps à répondre.',
                'error.internalServer': 'Une erreur serveur s\'est produite. Veuillez réessayer plus tard.',
                'error.gatewayTimeout': 'Délai d\'attente de la passerelle expiré. La conversion prend plus de temps que prévu.',
                'error.networkError': 'Erreur réseau. Veuillez vérifier votre connexion internet.',
                'error.connectionRefused': 'Impossible de se connecter au serveur. Veuillez réessayer plus tard.',
                'error.timeout': 'Délai d\'attente expiré. Veuillez réessayer avec un fichier plus petit ou plus tard.',
                'error.unknown': 'Une erreur inconnue s\'est produite : {message}',
                // WebSocket-specific translations
                'ws.connecting': 'Connexion en cours...',
                'ws.connected': 'Connecté',
                'ws.disconnected': 'Déconnecté - reconnexion...',
                'ws.reconnected': 'Reconnecté',
                'ws.error': 'Erreur WebSocket',
                'progress.office': 'Conversion du document Office en PDF...',
                'progress.scanning': 'Analyse de la structure PDF...',
                'progress.ocr': 'Traitement OCR : page {current} sur {total}',
                'progress.pdfa': 'Conversion au format PDF/A...',
                'button.cancel': 'Annuler',
                'status.queued': 'En file d\'attente - en attente de traitement...',
                'status.processing': 'Traitement en cours...',
                'status.cancelling': 'Annulation...',
                'status.cancelled': 'Conversion annulée',
                'error.job_timeout': 'Délai de conversion dépassé',
                'error.job_cancelled': 'Le travail a été annulé',
                'error.ws_connection': 'Échec de la connexion WebSocket',
                // Auth-related translations
                'auth.signInTitle': 'Connectez-vous pour continuer',
                'auth.signInMessage': 'L\'authentification est requise pour utiliser le convertisseur PDF/A',
                'auth.signInWithGoogle': 'Se connecter avec Google',
                'auth.loginFailed': 'Échec de l\'authentification. Veuillez réessayer.',
                'auth.downloadFailed': 'Échec du téléchargement. Veuillez réessayer.',
                'auth.viewPdfFailed': 'Impossible d\'ouvrir le PDF. Veuillez réessayer.',
                // Écran de bienvenue
                'welcome.title': 'Convertisseur PDF/A',
                'welcome.description': 'Service professionnel de conversion de documents avec support OCR. Convertissez vos PDFs, documents Office et images au format d\'archivage PDF/A - garantissant l\'accessibilité à long terme et la conformité aux normes internationales.',
                'welcome.feature1.title': 'Sécurisé et Privé',
                'welcome.feature1.description': 'Vos documents sont traités en toute sécurité et ne sont jamais stockés de manière permanente',
                'welcome.feature2.title': 'OCR Multilingue',
                'welcome.feature2.description': 'Support pour l\'anglais, l\'allemand, le français, l\'espagnol, l\'italien et plus',
                'welcome.feature3.title': 'Capture par Caméra',
                'welcome.feature3.description': 'Numérisez les documents directement avec l\'appareil photo de votre appareil',
                'welcome.feature4.title': 'Accessibilité',
                'welcome.feature4.description': 'Guidage audio et support de lecteur d\'écran pour les utilisateurs malvoyants',
                'welcome.cta': 'Veuillez vous connecter pour commencer à convertir vos documents.',
                // Étiquettes des onglets
                'tabs.konverter': 'Convertisseur',
                'tabs.kamera': 'Caméra',
                'tabs.auftraege': 'Tâches',
                'tabs.konto': 'Compte',
                'tabs.dokumentation': 'Documentation',
                // Contenu de l'espace réservé
                'placeholder.kamera.title': 'Scanner de Caméra',
                'placeholder.kamera.description': 'Bientôt disponible : Téléchargez des documents directement depuis votre caméra ou scanner',
                // Traductions de l'onglet Caméra
                'camera.start': 'Démarrer la Caméra',
                'camera.stop': 'Arrêter la Caméra',
                'camera.capture': 'Capturer',
                'camera.switch': 'Changer de Caméra',
                'camera.selectCamera': 'Sélectionner la Caméra:',
                'camera.pages.title': 'Pages',
                'camera.pages.add': 'Ajouter une Page',
                'camera.pages.clear': 'Tout Effacer',
                'camera.pages.submit': 'Convertir en PDF/A',
                'camera.settings.title': 'Paramètres de Conversion',
                // Traductions d'accessibilité
                'camera.a11y.title': 'Assistance d\'Accessibilité',
                'camera.a11y.enable': 'Activer le guidage audio',
                'camera.a11y.helpText': 'Fournit un retour audio pour la détection des bords',
                'camera.a11y.volume': 'Volume',
                'camera.a11y.test': 'Tester l\'Audio',
                'camera.a11y.testAnnouncement': 'Test audio. Si vous pouvez entendre ceci, l\'audio fonctionne.',
                'camera.a11y.loading': 'Chargement des fonctionnalités d\'accessibilité...',
                'camera.a11y.statusReady': 'Prêt à numériser',
                'camera.a11y.edgesDetected': 'Bords du document détectés. Tenez fermement.',
                'camera.a11y.edgesLost': 'Bords perdus. Ajustez la position de la caméra.',
                'camera.a11y.topEdge': 'Bord supérieur',
                'camera.a11y.bottomEdge': 'Bord inférieur',
                'camera.a11y.leftEdge': 'Bord gauche',
                'camera.a11y.rightEdge': 'Bord droit',
                'camera.a11y.notVisible': 'non visible',
                'camera.a11y.moveCloser': 'Rapprochez-vous du document',
                'camera.a11y.moveFarther': 'Éloignez-vous du document',
                'camera.a11y.enabled': 'Assistance caméra activée',
                'camera.a11y.disabled': 'Assistance caméra désactivée',
                'camera.a11y.enableAutoCapture': 'Activer la capture automatique',
                'camera.a11y.autoCaptureHelp': 'Prend automatiquement une photo après 2 secondes lorsque le document est centré',
                'camera.a11y.holdSteady': 'Tenez la caméra fermement',
                'camera.a11y.centerDocument': 'Centrez le document',
                'camera.a11y.photoCaptured': 'Photo capturée',
                'camera.edit.rotation': 'Rotation',
                'camera.edit.rotateLeft': '↺ 90° Gauche',
                'camera.edit.rotateRight': '↻ 90° Droite',
                'camera.edit.adjustments': 'Ajustements',
                'camera.edit.brightness': 'Luminosité',
                'camera.edit.contrast': 'Contraste',
                'camera.edit.crop': 'Recadrer',
                'camera.edit.cropButton': '✂️ Recadrer (Bientôt)',
                'camera.edit.cropHint': 'Faites glisser sur le canevas pour sélectionner une zone',
                'camera.edit.accept': '✓ Accepter',
                'camera.edit.retake': '✗ Reprendre',
                'camera.errors.noCamera': 'Aucune caméra trouvée',
                'camera.errors.permissionDenied': 'Autorisation de caméra refusée',
                'camera.errors.noPages': 'Veuillez capturer au moins une page',
                'placeholder.auftraege.title': 'Historique des Tâches',
                'placeholder.auftraege.description': 'Bientôt disponible : Consultez et gérez votre historique de conversion',
                'placeholder.konto.title': 'Paramètres du Compte',
                'placeholder.konto.description': 'Bientôt disponible : Gérez vos préférences et paramètres de compte',
                'placeholder.dokumentation.title': 'Documentation',
                'placeholder.dokumentation.description': 'Bientôt disponible : Guides d\'utilisation et documentation d\'aide',
                // Traductions de l'onglet Tâches
                'jobs.title': 'Historique des Tâches',
                'jobs.loading': 'Chargement des tâches...',
                'jobs.retry': 'Réessayer',
                'jobs.refresh': 'Actualiser',
                'jobs.autoRefresh.on': 'Actualisation Auto: ACTIVÉE',
                'jobs.autoRefresh.off': 'Actualisation Auto: DÉSACTIVÉE',
                'jobs.filter.all': 'Tous',
                'jobs.filter.completed': 'Terminés',
                'jobs.filter.failed': 'Échoués',
                'jobs.filter.processing': 'En cours',
                'jobs.table.status': 'Statut',
                'jobs.table.filename': 'Nom du fichier',
                'jobs.table.created': 'Créé',
                'jobs.table.duration': 'Durée',
                'jobs.table.size': 'Taille',
                'jobs.table.events': 'Événements',
                'jobs.table.actions': 'Actions',
                'jobs.status.completed': 'Terminé',
                'jobs.status.failed': 'Échoué',
                'jobs.status.processing': 'En cours',
                'jobs.status.queued': 'En attente',
                'jobs.status.cancelled': 'Annulé',
                'jobs.actions.download': 'Télécharger',
                'jobs.actions.retry': 'Réessayer',
                'jobs.actions.expand': 'Développer les événements',
                'jobs.actions.collapse': 'Réduire les événements',
                'jobs.events.empty': 'Aucun événement enregistré pour cette tâche',
                'jobs.download.error': 'Échec du téléchargement. Veuillez réessayer.',
                'jobs.retry.notification': 'Veuillez télécharger {filename} pour réessayer cette conversion',
                'jobs.retry.error': 'Échec du chargement des détails de la tâche. Veuillez réessayer.',
                'jobs.empty.title': 'Aucune tâche trouvée',
                'jobs.empty.description': 'Vous n\'avez pas encore de tâches de conversion',
                'jobs.pagination.previous': 'Précédent',
                'jobs.pagination.next': 'Suivant',
                'jobs.pagination.info': '{start}-{end} sur {total} tâches',
                'jobs.time.year': 'il y a {value} an(s)',
                'jobs.time.month': 'il y a {value} mois',
                'jobs.time.week': 'il y a {value} semaine(s)',
                'jobs.time.day': 'il y a {value} jour(s)',
                'jobs.time.hour': 'il y a {value} heure(s)',
                'jobs.time.minute': 'il y a {value} minute(s)',
                'jobs.time.just_now': 'À l\'instant',
                // Traductions de la liste d'événements (clés plates pour HTML)
                'events.title': 'Événements de Conversion',
                'events.details': 'Détails',
                // Traductions des étapes de progression (étapes OCRmyPDF)
                progressSteps: {
                    'Starting conversion': 'Démarrage de la conversion',
                    'Office conversion': 'Conversion du document Office',
                    'Scanning contents': 'Analyse du contenu',
                    'OCR': 'Traitement OCR',
                    'PDF/A conversion': 'Conversion en PDF/A',
                    'Linearizing': 'Linéarisation',
                    'Recompressing JPEGs': 'Recompression des JPEGs',
                    'Deflating JPEGs': 'Décompression des JPEGs',
                    'JBIG2': 'Compression JBIG2',
                    'Optimize': 'Optimisation',
                    'Repair': 'Réparation du PDF'
                },
                // Messages d'événements (structure imbriquée pour JavaScript)
                events: {
                    messages: {
                        format_conversion: {
                            none: 'Aucune conversion de format requise (la source est PDF)',
                            docx: {
                                success: 'DOCX converti en PDF ({pages} pages)'
                            },
                            xlsx: {
                                success: 'XLSX converti en PDF ({pages} pages)'
                            },
                            pptx: {
                                success: 'PPTX converti en PDF ({pages} diapositives)'
                            },
                            odt: {
                                success: 'ODT converti en PDF ({pages} pages)'
                            },
                            generic: {
                                success: '{format} converti en PDF'
                            }
                        },
                        ocr_decision: {
                            skip: {
                                tagged_pdf: 'OCR ignoré: PDF déjà balisé',
                                text_detected: 'OCR ignoré: texte consultable détecté',
                                has_text: 'OCR ignoré: texte existant trouvé',
                                user_request: 'OCR ignoré: désactivé par l\'utilisateur'
                            },
                            perform: {
                                no_text: 'OCR sera effectué: aucun texte détecté'
                            },
                            apply: {
                                scanned_pdf: 'OCR appliqué: document numérisé détecté',
                                low_text_content: 'OCR appliqué: faible contenu textuel',
                                user_request: 'OCR appliqué: forcé par l\'utilisateur'
                            }
                        },
                        compression_selected: {
                            high: {
                                large_file: 'Compression élevée: taille du fichier {size_mb} MB',
                                user_request: 'Compression élevée: demandée par l\'utilisateur'
                            },
                            balanced: {
                                default: 'Compression équilibrée: compromis optimal qualité/taille'
                            },
                            low: {
                                small_file: 'Compression faible: taille du fichier {size_mb} MB',
                                user_request: 'Compression faible: priorité à la qualité'
                            }
                        },
                        passthrough_mode: {
                            valid_pdfa: {
                                pdfa_2b: 'Passthrough: déjà conforme PDF/A-2b',
                                pdfa_3b: 'Passthrough: déjà conforme PDF/A-3b'
                            }
                        },
                        fallback_applied: {
                            ocr_failed: {
                                skip_ocr: 'Fallback: OCR échoué, continuation sans OCR'
                            },
                            compression_failed: {
                                skip_compression: 'Fallback: compression échouée, utilisation de l\'original'
                            },
                            conversion_error: {
                                retry_simple: 'Fallback: erreur de conversion, nouvelle tentative avec paramètres simplifiés'
                            }
                        },
                        job_timeout: {
                            exceeded: {
                                max_duration: 'Expiration: durée maximale dépassée ({timeout_sec}s)'
                            }
                        },
                        job_cleanup: {
                            success: {
                                temp_files: 'Nettoyage: fichiers temporaires supprimés'
                            }
                        }
                    }
                },
                // Traductions du modal
                modal: {
                    title: 'Résumé de Conversion',
                    description: 'Votre document a été converti avec succès. Voici ce qui s\'est passé:',
                    downloadButton: '📥 Télécharger',
                    okButton: 'OK',
                    opened: 'Dialogue ouvert: Résumé de Conversion'
                },
                // Étiquettes de formulaire
                'form.pdfType': 'Type de PDF',
                'pdf.standard': 'PDF Standard',
                // Onglet Compte (Konto)
                'konto.loading': 'Chargement des informations de compte...',
                'konto.error': 'Échec du chargement des informations de compte',
                'konto.retry': 'Réessayer',
                'konto.accountInfo': 'Informations de Compte',
                'konto.profile': 'Profil',
                'konto.name': 'Nom',
                'konto.email': 'E-mail',
                'konto.userId': 'ID Utilisateur',
                'konto.loginStats': 'Statistiques de Connexion',
                'konto.accountCreated': 'Compte Créé',
                'konto.lastLogin': 'Dernière Connexion',
                'konto.totalLogins': 'Total de Connexions',
                'konto.jobStats': 'Statistiques de Conversion',
                'konto.totalJobs': 'Total de Tâches',
                'konto.successRate': 'Taux de Réussite',
                'konto.avgDuration': 'Durée Moyenne',
                'konto.dataProcessed': 'Données Traitées',
                'konto.recentActivity': 'Activité Récente',
                'konto.settings': 'Paramètres',
                'konto.defaultParams': 'Paramètres de Conversion par Défaut',
                'konto.defaultParamsDesc': 'Ces paramètres seront appliqués automatiquement lors de l\'ouverture du convertisseur.',
                'konto.savePreferences': 'Enregistrer les Préférences',
                'konto.resetDefaults': 'Réinitialiser aux Valeurs par Défaut',
                'konto.preferencesSaved': 'Préférences enregistrées avec succès',
                'konto.preferencesSaveFailed': 'Échec de l\'enregistrement des préférences',
                'konto.dangerZone': 'Zone Dangereuse',
                'konto.deleteAccount': 'Supprimer le Compte',
                'konto.deleteWarning': '⚠️ Cette action est irréversible. Cela supprimera définitivement votre compte, tous les travaux de conversion, journaux d\'activité et préférences.',
                'konto.deleteAccountBtn': 'Supprimer Mon Compte',
                'konto.deleteDisabled': 'La suppression de compte n\'est pas disponible en mode local.',
                'konto.confirmDelete': 'Confirmer la Suppression du Compte',
                'konto.confirmDeleteDesc': 'Pour confirmer la suppression, veuillez taper votre adresse e-mail ci-dessous :',
                'konto.emailMismatch': 'L\'e-mail ne correspond pas',
                'konto.cancel': 'Annuler',
                'konto.confirmDeleteBtn': 'Supprimer le Compte',
                'konto.accountDeleted': 'Compte supprimé avec succès. Vous serez déconnecté.',
                'konto.deleteFailed': 'Échec de la suppression du compte'
            }
};
