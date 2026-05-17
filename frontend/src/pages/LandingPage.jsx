import React from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Shield, Activity, ArrowRight } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-6 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/5 blur-3xl pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-secondary/5 blur-3xl pointer-events-none" />

      <div className="max-w-4xl w-full glass-panel p-10 md:p-16 relative z-10">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-3 bg-primary/10 text-primary rounded-2xl mb-6">
            <BookOpen size={32} />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-textMain mb-6 tracking-tight">
            Next-Gen Academic Assessment
          </h1>
          <p className="text-lg md:text-xl text-textMain/70 max-w-2xl mx-auto leading-relaxed">
            A secure, calm, and intelligent platform for remote examinations. Focus on your test while our transparent AI ensures academic integrity without intrusive surveillance.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="metric-card hover:-translate-y-1">
            <Shield className="text-secondary mb-4" size={24} />
            <h3 className="font-semibold text-lg mb-2 text-textMain">Secure Environment</h3>
            <p className="text-textMain/60 text-sm">Maintains academic standards with robust, non-invasive monitoring.</p>
          </div>
          <div className="metric-card hover:-translate-y-1">
            <Activity className="text-success mb-4" size={24} />
            <h3 className="font-semibold text-lg mb-2 text-textMain">Real-time Feedback</h3>
            <p className="text-textMain/60 text-sm">Provides continuous updates on focus, posture, and engagement.</p>
          </div>
          <div className="metric-card hover:-translate-y-1">
            <BookOpen className="text-primary mb-4" size={24} />
            <h3 className="font-semibold text-lg mb-2 text-textMain">Distraction Free</h3>
            <p className="text-textMain/60 text-sm">A clean interface designed to minimize stress and maximize focus.</p>
          </div>
        </div>

        <div className="text-center">
          <button
            onClick={() => navigate('/exam')}
            className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-primary hover:bg-primary/90 text-white rounded-xl font-medium text-lg transition-all duration-200 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30"
          >
            Start Examination
            <ArrowRight size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
