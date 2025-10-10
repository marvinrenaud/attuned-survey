import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Heart } from 'lucide-react';
import logo from '../assets/AttunedLogo.png';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background-primary">
      <div className="container mx-auto px-4 py-12">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex justify-center mb-6">
            <img src={logo} alt="Attuned" className="w-32 h-32 object-contain" />
          </div>
          <h1 className="text-5xl font-bold text-text-primary mb-4 font-heading">
            Attuned
          </h1>
          <p className="text-xl text-text-secondary max-w-2xl mx-auto">
            Discover your intimacy profile and explore what makes you uniquely you
          </p>
        </header>

        {/* Main Content */}
        <div className="max-w-3xl mx-auto bg-white rounded-2xl shadow-xl p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-tertiary rounded-full mb-4">
              <Heart className="w-8 h-8 text-primary" />
            </div>
            <h2 className="text-3xl font-bold text-text-primary mb-4 font-heading">
              Welcome to Your Intimacy Journey
            </h2>
            <p className="text-lg text-text-secondary mb-6">
              This survey helps you understand your unique intimacy profile—what excites you, 
              what grounds you, and how you connect with others.
            </p>
          </div>

          {/* What to Expect */}
          <div className="space-y-6 mb-8">
            <div className="border-l-4 border-secondary pl-4">
              <h3 className="font-semibold text-text-primary mb-2">What You'll Discover</h3>
              <ul className="space-y-2 text-text-secondary">
                <li>• Your intimacy archetype and what it means</li>
                <li>• Four key dimensions: Adventure, Connection, Intensity, and Confidence</li>
                <li>• How you align with others (if a baseline is set)</li>
              </ul>
            </div>

            <div className="border-l-4 border-secondary pl-4">
              <h3 className="font-semibold text-text-primary mb-2">The Survey</h3>
              <ul className="space-y-2 text-text-secondary">
                <li>• 5 chapters covering arousal, preferences, boundaries, and more</li>
                <li>• Takes about 15-20 minutes to complete</li>
                <li>• Your answers are saved automatically—you can pause and resume anytime</li>
                <li>• All data stays private in your browser</li>
              </ul>
            </div>

            <div className="border-l-4 border-secondary pl-4">
              <h3 className="font-semibold text-text-primary mb-2">Important Notes</h3>
              <ul className="space-y-2 text-text-secondary">
                <li>• Answer honestly—there are no right or wrong answers</li>
                <li>• Your boundaries are respected throughout</li>
                <li>• Results are for self-discovery and mutual understanding</li>
              </ul>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              onClick={() => navigate('/survey')}
              className="bg-gradient-to-r from-primary to-secondary hover:opacity-90 text-white px-8 py-6 text-lg"
            >
              Start Your Survey
            </Button>
            <Button
              variant="outline"
              onClick={() => navigate('/privacy')}
              className="border-primary text-primary hover:bg-tertiary px-8 py-6 text-lg"
            >
              Privacy Policy
            </Button>
          </div>
        </div>

        <footer className="text-center mt-12 text-sm text-text-secondary space-y-2">
          <p>
            <button 
              onClick={() => navigate('/admin')} 
              className="text-primary hover:text-secondary font-medium underline"
            >
              Admin Panel
            </button>
          </p>
          <p>Made with <a href="https://manus.im" target="_blank" rel="noopener noreferrer" className="text-secondary hover:text-primary font-medium">Manus</a></p>
        </footer>
      </div>
    </div>
  );
}

