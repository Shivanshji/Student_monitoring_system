import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Clock, AlertTriangle, Activity, User, Eye } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

const ExamPage = () => {
  const navigate = useNavigate();
  const [metrics, setMetrics] = useState(null);
  const [sessionActive, setSessionActive] = useState(false);
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    // Start session on mount
    const startSession = async () => {
      try {
        await axios.post(`${API_BASE_URL}/start-session`);
        setSessionActive(true);
        setLoading(false);
      } catch (error) {
        console.error("Failed to start session:", error);
        setLoading(false);
      }
    };
    startSession();

    return () => {
      // Cleanup on unmount
      if (sessionActive) {
        axios.post(`${API_BASE_URL}/end-session`).catch(console.error);
      }
    };
  }, []);

  useEffect(() => {
    // Poll metrics
    let interval;
    if (sessionActive) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE_URL}/metrics`);
          setMetrics(res.data);
        } catch (error) {
          console.error("Failed to fetch metrics:", error);
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [sessionActive]);

  useEffect(() => {
    // Timer
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (timeLeft === 0 && sessionActive) {
      handleEndExam();
    }
  }, [timeLeft, sessionActive]);

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleEndExam = async () => {
    try {
      const res = await axios.post(`${API_BASE_URL}/end-session`);
      setSummary(res.data.summary);
      setSessionActive(false);
    } catch (error) {
      console.error("Failed to end session:", error);
    }
  };

  const getStatusColor = (stateStr, metricType) => {
    if (!stateStr) return "text-textMain/50";
    const s = stateStr.toLowerCase();
    
    if (metricType === "attention") {
        if (s.includes("focused")) return "text-success";
        if (s.includes("distracted")) return "text-warning";
    }
    if (metricType === "posture") {
        if (s.includes("good")) return "text-success";
        if (s.includes("slouching")) return "text-warning";
        if (s.includes("leaning")) return "text-orange-500";
    }
    if (metricType === "motion") {
        if (s.includes("stable") || s.includes("slight")) return "text-success";
        if (s.includes("restless")) return "text-warning";
        if (s.includes("high")) return "text-orange-500";
    }
    return "text-textMain";
  };

  const renderWarning = () => {
    if (!metrics) return null;
    
    const warnings = [];
    
    // Low attention warning
    if (metrics.warning_triggered) {
      warnings.push(
        <div key="attention-warning" className="bg-amber-50 border border-amber-200 text-amber-800 px-4 py-3 rounded-xl flex items-start gap-3 mb-3">
          <AlertTriangle className="text-amber-600 flex-shrink-0 mt-0.5" size={18} />
          <div className="text-left">
            <p className="font-semibold text-xs text-amber-900 uppercase tracking-wider">Attention Notice</p>
            <p className="text-xs mt-0.5 text-amber-800">Your exam session may go under review before evaluation.</p>
          </div>
        </div>
      );
    }

    // Existing live error warnings
    if (!metrics.valid && metrics.error && metrics.error !== "Not started") {
        let msg = "";
        if (metrics.error === "no_face") msg = "Face not detected!";
        if (metrics.error === "multiple_faces") msg = "Multiple faces detected!";
        if (msg) {
            warnings.push(
                <div key="face-warning" className="bg-danger/10 border border-danger/30 text-danger px-4 py-3 rounded-xl flex items-center gap-3 mb-3 animate-pulse">
                    <AlertTriangle size={20} />
                    <span className="font-medium text-sm">{msg}</span>
                </div>
            );
        }
    }

    return warnings.length > 0 ? <div className="flex flex-col">{warnings}</div> : null;
  };

  const renderSummaryModal = () => {
    if (!summary) return null;
    return (
      <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl overflow-hidden border border-indigo-50 animate-in fade-in zoom-in duration-200">
          <div className="bg-primary p-6 text-white text-center">
            <h3 className="text-xl font-bold mb-1">Exam Submitted Successfully</h3>
            <p className="text-white/85 text-sm">Academic Integrity Session Report</p>
          </div>
          <div className="p-6 space-y-6">
            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-indigo-50">
                <span className="text-textMain/60 text-sm font-medium">Session ID</span>
                <span className="font-mono text-sm text-textMain font-semibold">{summary.session_id}</span>
              </div>
              <div className="flex justify-between items-center pb-3 border-b border-indigo-50">
                <span className="text-textMain/60 text-sm font-medium">Average Attention</span>
                <span className="text-lg font-bold text-primary">{summary.average_attention}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-textMain/60 text-sm font-medium">Average Engagement</span>
                <span className="text-lg font-bold text-primary">{summary.average_engagement}%</span>
              </div>
            </div>

            {summary.warning_triggered ? (
              <div className="bg-warning/10 border border-warning/30 rounded-xl p-4 flex gap-3 text-warning text-left animate-pulse">
                <AlertTriangle className="flex-shrink-0 mt-0.5" size={18} />
                <div>
                  <h4 className="font-semibold text-sm">Under Review</h4>
                  <p className="text-xs text-warning/90">This session has been flagged for review due to low attention levels.</p>
                </div>
              </div>
            ) : (
              <div className="bg-success/5 border border-success/15 rounded-xl p-4 flex gap-3 text-success text-left">
                <Activity className="flex-shrink-0 mt-0.5 animate-pulse" size={18} />
                <div>
                  <h4 className="font-semibold text-sm">Session Verified</h4>
                  <p className="text-xs text-success/80">Academic integrity was successfully monitored throughout this assessment.</p>
                </div>
              </div>
            )}

            <button
              onClick={() => navigate('/')}
              className="w-full py-3 bg-primary hover:bg-primary/90 text-white font-medium rounded-xl transition-all shadow-md"
            >
              Return to Homepage
            </button>
          </div>
        </div>
      </div>
    );
  };


  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-background text-textMain">Starting secure session...</div>;
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-6 flex flex-col md:flex-row gap-6">
      
      {/* Left Column: Exam Interface */}
      <div className="flex-1 glass-panel flex flex-col overflow-hidden">
        <div className="border-b border-indigo-50/50 p-4 px-6 flex justify-between items-center bg-white/50">
          <h2 className="font-bold text-xl">Computer Science Final 2026</h2>
          <div className="flex items-center gap-2 font-mono text-lg bg-indigo-50 text-primary px-4 py-2 rounded-lg">
            <Clock size={20} />
            {formatTime(timeLeft)}
          </div>
        </div>
        
        <div className="p-8 flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto space-y-10">
            {/* Dummy Question 1 */}
            <div className="space-y-4">
              <div className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-primary text-white rounded-full font-medium shadow-sm">1</span>
                <div className="w-full">
                  <h3 className="font-medium text-lg mb-4 text-textMain">Explain the concept of Big O notation and its importance in algorithm analysis. Provide examples of O(1), O(n), and O(n^2) algorithms.</h3>
                  <textarea 
                    className="w-full h-40 p-4 rounded-xl border border-indigo-100 bg-white/80 focus:bg-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-none shadow-inner"
                    placeholder="Type your answer here..."
                  ></textarea>
                </div>
              </div>
            </div>

            {/* Dummy Question 2 */}
            <div className="space-y-4">
              <div className="flex gap-4">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-primary text-white rounded-full font-medium shadow-sm">2</span>
                <div className="w-full">
                  <h3 className="font-medium text-lg mb-4 text-textMain">What is a dead-lock in operating systems? Describe the four necessary conditions for a deadlock to occur.</h3>
                  <textarea 
                    className="w-full h-40 p-4 rounded-xl border border-indigo-100 bg-white/80 focus:bg-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all resize-none shadow-inner"
                    placeholder="Type your answer here..."
                  ></textarea>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="p-4 px-6 border-t border-indigo-50/50 bg-white/50 flex justify-end">
          <button 
            onClick={handleEndExam}
            className="px-8 py-3 bg-primary hover:bg-primary/90 text-white rounded-xl font-medium transition-all shadow-md hover:shadow-lg"
          >
            Submit Examination
          </button>
        </div>
      </div>

      {/* Right Column: Monitoring Panel */}
      <div className="w-full md:w-80 flex flex-col gap-4 flex-shrink-0">
        {/* Video Feed */}
        <div className="glass-panel overflow-hidden relative">
          <div className="p-3 border-b border-indigo-50 bg-white/50 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${sessionActive ? 'bg-success animate-pulse' : 'bg-textMain/20'}`} />
            <span className="text-xs font-semibold uppercase tracking-wider text-textMain/70">Live Feed</span>
          </div>
          <div className="aspect-video bg-slate-900 relative">
            {sessionActive ? (
               <img 
                 src={`${API_BASE_URL}/video-feed`} 
                 alt="Monitoring Feed" 
                 className="w-full h-full object-cover"
                 onError={(e) => {
                     e.target.style.display = 'none';
                 }}
               />
            ) : (
               <div className="absolute inset-0 flex items-center justify-center text-white/50 text-sm">
                 Feed offline
               </div>
            )}
          </div>
        </div>

        {/* Warnings */}
        {renderWarning()}

        {/* Metrics */}
        <div className="glass-panel p-5 flex-1">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-textMain/60 mb-6 flex items-center gap-2">
            <Activity size={16} />
            Session Metrics
          </h3>
          
          <div className="space-y-6">
            
            <div>
              <div className="flex justify-between items-end mb-2">
                <span className="text-sm font-medium text-textMain/80">Engagement Score</span>
                <span className="text-2xl font-bold text-primary">{metrics?.engagement || 0}%</span>
              </div>
              <div className="w-full h-2 bg-indigo-50 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-500 ease-out"
                  style={{ width: `${metrics?.engagement || 0}%` }}
                />
              </div>
            </div>

          </div>
        </div>
      </div>
      {renderSummaryModal()}
    </div>
  );
};

export default ExamPage;
