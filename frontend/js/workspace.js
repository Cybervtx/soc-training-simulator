/**
 * Workspace JavaScript - SOC Training Simulator (Parte 2)
 * Vue.js application for investigation workspace
 */

const { createApp, ref, computed, onMounted, onUnmounted, watch } = Vue;

const app = createApp({
    setup() {
        // State
        const loading = ref(true);
        const error = ref(null);
        const scenarioId = ref(null);
        const scenario = ref(null);
        const artifacts = ref([]);
        const timeline = ref([]);
        const notes = ref([]);
        
        // UI State
        const activeTab = ref('brief');
        const timelineFilter = ref('all');
        const artifactFilter = ref('all');
        const selectedArtifact = ref(null);
        const selectedEvent = ref(null);
        const showSubmitModal = ref(false);
        
        // Timer
        const startTime = ref(null);
        const elapsedSeconds = ref(0);
        let timerInterval = null;
        
        // Tool queries and results
        const toolQueries = ref({
            geoip: '',
            whois: '',
            pdns: '',
            shodan: ''
        });
        
        const toolResults = ref({
            geoip: null,
            whois: null,
            pdns: null,
            shodan: null
        });
        
        // Submission data
        const submission = ref({
            conclusions: '',
            recommendations: ''
        });
        
        // Computed properties
        const groupedTimeline = computed(() => {
            const grouped = {};
            for (const event of timeline.value) {
                const date = new Date(event.timestamp).toISOString().split('T')[0];
                if (!grouped[date]) {
                    grouped[date] = [];
                }
                grouped[date].push(event);
            }
            return grouped;
        });
        
        const filteredTimeline = computed(() => {
            if (timelineFilter.value === 'all') {
                return timeline.value;
            }
            const priorityMap = { 'high': 3, 'medium': 2, 'low': 1 };
            const filterPriority = priorityMap[timelineFilter.value];
            return timeline.value.filter(e => e.priority === filterPriority);
        });
        
        const filteredArtifacts = computed(() => {
            if (artifactFilter.value === 'all') {
                return artifacts.value;
            }
            if (artifactFilter.value === 'malicious') {
                return artifacts.value.filter(a => a.is_malicious);
            }
            if (artifactFilter.value === 'benign') {
                return artifacts.value.filter(a => !a.is_malicious);
            }
            if (artifactFilter.value === 'critical') {
                return artifacts.value.filter(a => a.is_critical);
            }
            return artifacts.value;
        });
        
        const isInvestigationActive = computed(() => {
            return scenario.value !== null && startTime.value !== null;
        });
        
        const elapsedTime = computed(() => {
            const hours = Math.floor(elapsedSeconds.value / 3600);
            const minutes = Math.floor((elapsedSeconds.value % 3600) / 60);
            const seconds = elapsedSeconds.value % 60;
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        });
        
        // Methods
        const loadScenario = async () => {
            loading.value = true;
            error.value = null;
            
            try {
                // Get scenario ID from URL or use demo scenario
                const urlParams = new URLSearchParams(window.location.search);
                scenarioId.value = urlParams.get('id') || 'demo-scenario';
                
                // Load scenario data
                const response = await axios.get(`/api/scenarios/${scenarioId.value}`);
                
                if (response.data.success) {
                    const data = response.data.data;
                    scenario.value = data.scenario;
                    artifacts.value = data.artifacts.map(a => ({
                        ...a,
                        status: a.status || 'investigating'
                    }));
                    timeline.value = data.timeline;
                    
                    // Start timer
                    startTimer();
                } else {
                    throw new Error(response.data.error || 'Failed to load scenario');
                }
            } catch (err) {
                console.error('Error loading scenario:', err);
                error.value = err.response?.data?.error || err.message || 'Unknown error';
                
                // Load demo data for testing
                loadDemoData();
            } finally {
                loading.value = false;
            }
        };
        
        const loadDemoData = () => {
            // Load demo scenario for testing
            scenario.value = {
                id: 'demo',
                title: 'Port Scanning Detection - Demo',
                description: 'Our network monitoring systems detected suspicious port scanning activity originating from an external IP address. Analyze the logs, identify the scanning patterns, and determine if this is malicious reconnaissance or legitimate activity.',
                difficulty: 'beginner',
                incident_type: 'port_scanning',
                estimated_duration: 30,
                learning_objectives: [
                    'Identify port scanning patterns in network logs',
                    'Differentiate between reconnaissance and active attacks',
                    'Trace attack source using log analysis',
                    'Recommend network segmentation strategies'
                ]
            };
            
            artifacts.value = [
                {
                    id: '1',
                    type: 'ip',
                    value: '185.220.101.42',
                    is_malicious: true,
                    is_critical: true,
                    points: 25,
                    status: 'investigating'
                },
                {
                    id: '2',
                    type: 'ip',
                    value: '8.8.8.8',
                    is_malicious: false,
                    is_critical: false,
                    points: 5,
                    status: 'confirmed'
                },
                {
                    id: '3',
                    type: 'domain',
                    value: 'scanner.badssl.com',
                    is_malicious: false,
                    is_critical: false,
                    points: 10,
                    status: 'investigating'
                }
            ];
            
            timeline.value = [
                {
                    id: 't1',
                    timestamp: new Date(Date.now() - 3600000).toISOString(),
                    event_type: 'network_scan',
                    description: 'Initial SYN packet detected from external IP',
                    source_ip: '185.220.101.42',
                    destination_ip: '10.0.0.5',
                    destination_port: 22,
                    priority: 2,
                    raw_log: '2025-02-11T10:00:00Z DENY TCP 185.220.101.42:12345 -> 10.0.0.5:22'
                },
                {
                    id: 't2',
                    timestamp: new Date(Date.now() - 3500000).toISOString(),
                    event_type: 'connection_attempt',
                    description: 'Connection attempt to port 22',
                    source_ip: '185.220.101.42',
                    destination_ip: '10.0.0.5',
                    destination_port: 22,
                    priority: 2,
                    raw_log: '2025-02-11T10:00:05Z DENY TCP 185.220.101.42:12346 -> 10.0.0.5:22'
                },
                {
                    id: 't3',
                    timestamp: new Date(Date.now() - 3400000).toISOString(),
                    event_type: 'connection_attempt',
                    description: 'Connection attempt to port 80',
                    source_ip: '185.220.101.42',
                    destination_ip: '10.0.0.5',
                    destination_port: 80,
                    priority: 2,
                    raw_log: '2025-02-11T10:00:10Z DENY TCP 185.220.101.42:12347 -> 10.0.0.5:80'
                },
                {
                    id: 't4',
                    timestamp: new Date(Date.now() - 3300000).toISOString(),
                    event_type: 'network_scan',
                    description: 'Rapid connection attempts detected - port scanning behavior',
                    source_ip: '185.220.101.42',
                    destination_ip: '10.0.0.5',
                    destination_port: 443,
                    priority: 3,
                    raw_log: '2025-02-11T10:00:15Z DENY TCP 185.220.101.42:12348 -> 10.0.0.5:443'
                }
            ];
            
            startTimer();
        };
        
        const startTimer = () => {
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            startTime.value = Date.now();
            elapsedSeconds.value = 0;
            timerInterval = setInterval(() => {
                elapsedSeconds.value++;
            }, 1000);
        };
        
        const stopTimer = () => {
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
        };
        
        const formatDate = (dateStr) => {
            const date = new Date(dateStr);
            return date.toLocaleDateString('pt-BR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        };
        
        const formatTime = (dateStr) => {
            const date = new Date(dateStr);
            return date.toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        };
        
        const getDifficultyLabel = (difficulty) => {
            const labels = {
                'beginner': 'Iniciante',
                'intermediate': 'Intermediário',
                'advanced': 'Avançado'
            };
            return labels[difficulty] || difficulty;
        };
        
        const getIncidentTypeLabel = (type) => {
            const labels = {
                'port_scanning': 'Port Scanning',
                'brute_force': 'Brute Force',
                'c2_communication': 'C2 Communication',
                'malware_distribution': 'Malware Distribution',
                'phishing_campaign': 'Phishing Campaign',
                'data_exfiltration': 'Data Exfiltration',
                'apt_activity': 'APT Activity'
            };
            return labels[type] || type;
        };
        
        const getEventTypeLabel = (type) => {
            const labels = {
                'network_scan': 'Network Scan',
                'connection_attempt': 'Connection Attempt',
                'authentication_failure': 'Authentication Failure',
                'authentication_success': 'Authentication Success',
                'c2_beacon': 'C2 Beacon',
                'file_download': 'File Download',
                'data_exfiltration': 'Data Exfiltration'
            };
            return labels[type] || type;
        };
        
        const getEventIcon = (type) => {
            const icons = {
                'network_scan': 'fa-radar',
                'connection_attempt': 'fa-plug',
                'authentication_failure': 'fa-key',
                'authentication_success': 'fa-check-circle',
                'c2_beacon': 'fa-satellite-dish',
                'file_download': 'fa-download',
                'data_exfiltration': 'fa-file-export'
            };
            return `fas ${icons[type] || 'fa-circle'}`;
        };
        
        const getArtifactIcon = (type) => {
            const icons = {
                'ip': 'fa-globe',
                'domain': 'fa-globe-americas',
                'url': 'fa-link',
                'file_hash': 'fa-file',
                'email': 'fa-envelope'
            };
            return `fas ${icons[type] || 'fa-file'}`;
        };
        
        const getStatusLabel = (status) => {
            const labels = {
                'investigating': 'Investigando',
                'confirmed': 'Confirmado',
                'false_positive': 'Falso Positivo'
            };
            return labels[status] || status;
        };
        
        const filteredEvents = (events) => {
            if (timelineFilter.value === 'all') {
                return events;
            }
            const priorityMap = { 'high': 3, 'medium': 2, 'low': 1 };
            const filterPriority = priorityMap[timelineFilter.value];
            return events.filter(e => e.priority === filterPriority);
        };
        
        const selectArtifact = (artifact) => {
            selectedArtifact.value = artifact;
            selectedEvent.value = null;
        };
        
        const selectEvent = (event) => {
            selectedEvent.value = event;
            selectedArtifact.value = null;
        };
        
        const closeDetails = () => {
            selectedArtifact.value = null;
            selectedEvent.value = null;
        };
        
        const setArtifactStatus = async (artifact, status) => {
            artifact.status = status;
            // Save to backend
            try {
                await axios.patch(`/api/scenarios/${scenarioId.value}/artifacts/${artifact.id}`, {
                    status: status
                });
            } catch (err) {
                console.error('Error updating artifact status:', err);
            }
        };
        
        const enrichArtifact = async () => {
            if (!selectedArtifact.value) return;
            
            try {
                const response = await axios.get('/api/tools/enrich', {
                    params: {
                        type: selectedArtifact.value.type,
                        value: selectedArtifact.value.value
                    }
                });
                
                if (response.data.success) {
                    selectedArtifact.value.enrichment = response.data.data;
                    // Show enrichment in a modal or expand details
                    alert('Dados de enriquecimento carregados! Veja os detalhes.');
                }
            } catch (err) {
                console.error('Error enriching artifact:', err);
                alert('Erro ao enriquecer artefato');
            }
        };
        
        // Tool lookup functions
        const lookupGeoIP = async () => {
            if (!toolQueries.value.geoip) return;
            
            try {
                const response = await axios.get('/api/tools/geoip', {
                    params: { ip: toolQueries.value.geoip }
                });
                
                if (response.data.success) {
                    toolResults.value.geoip = response.data.data;
                }
            } catch (err) {
                console.error('Error looking up GeoIP:', err);
            }
        };
        
        const lookupWhois = async () => {
            if (!toolQueries.value.whois) return;
            
            try {
                const response = await axios.get('/api/tools/whois', {
                    params: { domain: toolQueries.value.whois }
                });
                
                if (response.data.success) {
                    toolResults.value.whois = response.data.data;
                }
            } catch (err) {
                console.error('Error looking up WHOIS:', err);
            }
        };
        
        const lookupPDNS = async () => {
            if (!toolQueries.value.pdns) return;
            
            try {
                const response = await axios.get('/api/tools/pdns', {
                    params: { domain: toolQueries.value.pdns }
                });
                
                if (response.data.success) {
                    toolResults.value.pdns = response.data.data;
                }
            } catch (err) {
                console.error('Error looking up PDNS:', err);
            }
        };
        
        const lookupShodan = async () => {
            if (!toolQueries.value.shodan) return;
            
            try {
                const response = await axios.get('/api/tools/shodan', {
                    params: { ip: toolQueries.value.shodan }
                });
                
                if (response.data.success) {
                    toolResults.value.shodan = response.data.data;
                }
            } catch (err) {
                console.error('Error looking up Shodan:', err);
            }
        };
        
        // Notes
        const addNote = () => {
            notes.value.push({
                id: Date.now().toString(),
                content: '',
                tags: [],
                created_at: new Date().toISOString()
            });
        };
        
        const updateNote = async (note) => {
            try {
                await axios.post(`/api/scenarios/${scenarioId.value}/notes`, {
                    content: note.content,
                    tags: note.tags
                });
            } catch (err) {
                console.error('Error saving note:', err);
            }
        };
        
        const deleteNote = (noteId) => {
            notes.value = notes.value.filter(n => n.id !== noteId);
        };
        
        // Progress and submission
        const saveProgress = async () => {
            try {
                await axios.post(`/api/scenarios/${scenarioId.value}/start`);
                alert('Progresso salvo com sucesso!');
            } catch (err) {
                console.error('Error saving progress:', err);
                alert('Erro ao salvar progresso');
            }
        };
        
        const submitInvestigation = () => {
            showSubmitModal.value = true;
        };
        
        const confirmSubmission = async () => {
            try {
                await axios.post(`/api/scenarios/${scenarioId.value}/submit`, {
                    conclusions: submission.value.conclusions,
                    recommendations: submission.value.recommendations,
                    notes: notes.value
                });
                
                alert('Investigação submetida com sucesso!');
                showSubmitModal.value = false;
                stopTimer();
                
                // Redirect to dashboard
                window.location.href = '/pages/dashboard.html';
            } catch (err) {
                console.error('Error submitting investigation:', err);
                alert('Erro ao submeter investigação');
            }
        };
        
        // Lifecycle
        onMounted(() => {
            loadScenario();
        });
        
        onUnmounted(() => {
            stopTimer();
        });
        
        return {
            // State
            loading,
            error,
            scenario,
            artifacts,
            timeline,
            notes,
            
            // UI State
            activeTab,
            timelineFilter,
            artifactFilter,
            selectedArtifact,
            selectedEvent,
            showSubmitModal,
            
            // Timer
            elapsedTime,
            isInvestigationActive,
            
            // Tools
            toolQueries,
            toolResults,
            
            // Submission
            submission,
            
            // Computed
            groupedTimeline,
            filteredTimeline,
            filteredArtifacts,
            
            // Methods
            loadScenario,
            formatDate,
            formatTime,
            getDifficultyLabel,
            getIncidentTypeLabel,
            getEventTypeLabel,
            getEventIcon,
            getArtifactIcon,
            getStatusLabel,
            filteredEvents,
            selectArtifact,
            selectEvent,
            closeDetails,
            setArtifactStatus,
            enrichArtifact,
            lookupGeoIP,
            lookupWhois,
            lookupPDNS,
            lookupShodan,
            addNote,
            updateNote,
            deleteNote,
            saveProgress,
            submitInvestigation,
            confirmSubmission
        };
    }
});

app.mount('#app');
