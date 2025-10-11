import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { getSurveyChapters, validateChapter, getSchema } from '../lib/surveyData';
import { computeTraits, scoreArchetypes, getTopArchetypes } from '../lib/scoring/calculator';
import { saveSubmission, saveCurrentSession, getCurrentSession, clearCurrentSession } from '../lib/storage/apiStore';

export default function Survey() {
  const navigate = useNavigate();
  const [chapters] = useState(getSurveyChapters());
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [name, setName] = useState('');
  const [errors, setErrors] = useState([]);
  const [showNameInput, setShowNameInput] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentChapter = chapters[currentChapterIndex];
  // Progress starts at 0% and increases as user completes chapters
  // Calculate based on completed chapters (not current chapter)
  const progress = showNameInput ? 0 : (currentChapterIndex / chapters.length) * 100;

  // Load session on mount
  useEffect(() => {
    const session = getCurrentSession();
    if (session) {
      setAnswers(session.answers || {});
      setCurrentChapterIndex(session.currentChapter || 0);
      setName(session.name || '');
      if (session.name) setShowNameInput(false);
    }
  }, []);

  // Save session on changes
  useEffect(() => {
    if (name || Object.keys(answers).length > 0) {
      saveCurrentSession({
        answers,
        currentChapter: currentChapterIndex,
        name
      });
    }
  }, [answers, currentChapterIndex, name]);

  const handleAnswer = (itemId, value) => {
    setAnswers(prev => ({
      ...prev,
      [itemId]: value
    }));
    setErrors([]);
  };

  const handleNameSubmit = () => {
    if (!name.trim()) {
      setErrors(['Please enter your name to continue']);
      return;
    }
    setShowNameInput(false);
  };

  const handleNext = () => {
    // Validate current chapter
    const chapterErrors = validateChapter(currentChapter.items, answers);
    if (chapterErrors.length > 0) {
      setErrors(chapterErrors);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setErrors([]);

    if (currentChapterIndex < chapters.length - 1) {
      setCurrentChapterIndex(prev => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      handleSubmit();
    }
  };

  const handlePrevious = () => {
    if (currentChapterIndex > 0) {
      setCurrentChapterIndex(prev => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSubmit = async () => {
    // Prevent double submission
    if (isSubmitting) {
      console.log('Submission already in progress, ignoring duplicate click');
      return;
    }

    setIsSubmitting(true);
    setErrors([]);
    
    try {
      console.log('Starting survey submission...');
      
      // Calculate derived data
      const schema = getSchema();
      console.log('Schema loaded, calculating traits...');
      
      const traits = computeTraits(schema, answers);
      console.log('Traits calculated:', Object.keys(traits).length);
      
      const archetypeScores = scoreArchetypes(schema, traits);
      const topArchetypes = getTopArchetypes(archetypeScores, schema, 3);
      console.log('Archetypes calculated:', topArchetypes.map(a => a.name));

      // Generate unique ID with timestamp + random component to avoid collisions
      const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      const submission = {
        id: uniqueId,
        name,
        createdAt: new Date().toISOString(),
        answers,
        derived: {
          traits,
          archetypes: topArchetypes
        }
      };

      console.log('Submitting to API...', { id: submission.id, name: submission.name });
      const savedSubmission = await saveSubmission(submission);
      console.log('✅ Submission saved successfully:', savedSubmission.id);
      
      clearCurrentSession();
      console.log('Navigating to results page...');
      
      navigate('/result', { state: { submissionId: savedSubmission.id } });
    } catch (error) {
      console.error('❌ Error submitting survey:', error);
      setErrors([`Failed to submit survey: ${error.message}. Please try again.`]);
      setIsSubmitting(false);
    }
  };

  if (showNameInput) {
    return (
      <div className="min-h-screen bg-background-primary flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full">
          <h2 className="text-2xl font-bold text-text-primary mb-4 font-heading">Before We Begin</h2>
          <p className="text-text-secondary mb-6">
            Please enter your name. This helps us personalize your results.
          </p>
          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Your Name</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="mt-1"
                onKeyPress={(e) => e.key === 'Enter' && handleNameSubmit()}
              />
            </div>
            {errors.length > 0 && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{errors[0]}</AlertDescription>
              </Alert>
            )}
            <Button 
              onClick={handleNameSubmit}
              className="w-full bg-gradient-to-r from-primary to-secondary hover:opacity-90 text-white"
            >
              Continue
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background-primary">
      {/* Sticky Header */}
      <div className="sticky top-0 z-10 bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-bold text-text-primary font-heading" data-testid={`chapter-${currentChapter.id}-header`}>
              {currentChapter.title}
            </h1>
            <span className="text-sm text-text-secondary">
              Chapter {currentChapterIndex + 1} of {chapters.length}
            </span>
          </div>
          {/* Progress Bar */}
          <div className="space-y-1">
            <div className="flex justify-between items-center text-xs text-text-secondary">
              <span>Progress</span>
              <span className="font-medium">{Math.round(progress)}% Complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2" data-testid="progress-bar">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        {errors.length > 0 && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside">
                {errors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <div className="bg-white rounded-lg shadow-lg p-6 md:p-8">
          {/* Chapter description - sticky at top of card */}
          <div className="sticky top-20 bg-white pb-4 mb-4 border-b border-gray-200 -mx-6 -mt-6 px-6 pt-6 z-5">
            <p className="text-text-secondary font-medium">{currentChapter.description}</p>
          </div>

          <div className="space-y-8">
            {currentChapter.items.map((item) => (
              <QuestionItem
                key={item.id}
                item={item}
                value={answers[item.id]}
                onChange={(value) => handleAnswer(item.id, value)}
              />
            ))}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentChapterIndex === 0}
            className="border-primary text-primary hover:bg-tertiary"
            data-testid="prev-chapter"
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          <Button
            onClick={handleNext}
            disabled={isSubmitting}
            className="bg-gradient-to-r from-primary to-secondary hover:opacity-90 text-white disabled:opacity-50"
            data-testid={currentChapterIndex === chapters.length - 1 ? "submit" : "next-chapter"}
          >
            {isSubmitting ? 'Submitting...' : (currentChapterIndex === chapters.length - 1 ? 'Submit' : 'Next')}
            {currentChapterIndex < chapters.length - 1 && !isSubmitting && <ChevronRight className="w-4 h-4 ml-2" />}
          </Button>
        </div>
      </div>

      <footer className="text-center py-8 text-sm text-text-secondary">
        <p>Made with ♥️ in BK</p>
      </footer>
    </div>
  );
}

function QuestionItem({ item, value, onChange }) {
  if (item.type === 'likert7') {
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <RadioGroup value={value?.toString()} onValueChange={(v) => onChange(Number(v))}>
          <div className="grid grid-cols-7 gap-2">
            {[1, 2, 3, 4, 5, 6, 7].map((num) => (
              <div key={num} className="flex flex-col items-center">
                <RadioGroupItem value={num.toString()} id={`${item.id}-${num}`} className="mb-1" />
                <Label htmlFor={`${item.id}-${num}`} className="text-xs text-text-secondary cursor-pointer">
                  {num}
                </Label>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-text-secondary mt-2">
            <span>Strongly Disagree</span>
            <span>Neutral</span>
            <span>Strongly Agree</span>
          </div>
        </RadioGroup>
      </div>
    );
  }

  if (item.type === 'ymn') {
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <RadioGroup value={value} onValueChange={onChange}>
          <div className="flex gap-6">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="Y" id={`${item.id}-Y`} />
              <Label htmlFor={`${item.id}-Y`} className="cursor-pointer">Yes</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="M" id={`${item.id}-M`} />
              <Label htmlFor={`${item.id}-M`} className="cursor-pointer">Maybe</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="N" id={`${item.id}-N`} />
              <Label htmlFor={`${item.id}-N`} className="cursor-pointer">No</Label>
            </div>
          </div>
        </RadioGroup>
      </div>
    );
  }

  if (item.type === 'slider') {
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <div className="flex items-center gap-4">
          <input
            type="range"
            min="0"
            max="100"
            value={value || 50}
            onChange={(e) => onChange(Number(e.target.value))}
            className="flex-1"
          />
          <span className="text-sm font-medium text-text-primary w-12 text-right">{value || 50}</span>
        </div>
      </div>
    );
  }

  if (item.type === 'boundary') {
    if (item.id === 'C2') {
      // Hard NOs - multi-select checkboxes
      const options = ['impact', 'bondage', 'exhibition', 'voyeur', 'roleplay', 'recording', 'group/enm', 'public-edge', 'toys'];
      const selected = value ? value.split(',').map(s => s.trim()) : [];
      
      const handleToggle = (option) => {
        const newSelected = selected.includes(option)
          ? selected.filter(s => s !== option)
          : [...selected, option];
        onChange(newSelected.join(','));
      };

      return (
        <div data-testid={`item-${item.id}`}>
          <Label className="text-base font-medium text-text-primary mb-3 block">
            {item.text}
          </Label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {options.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id={`${item.id}-${option}`}
                  checked={selected.includes(option)}
                  onChange={() => handleToggle(option)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor={`${item.id}-${option}`} className="cursor-pointer capitalize">
                  {option}
                </Label>
              </div>
            ))}
          </div>
        </div>
      );
    }

    // Other boundary items - simple yes/no
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <RadioGroup value={value} onValueChange={onChange}>
          <div className="flex gap-6">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="Y" id={`${item.id}-Y`} />
              <Label htmlFor={`${item.id}-Y`} className="cursor-pointer">Yes</Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="N" id={`${item.id}-N`} />
              <Label htmlFor={`${item.id}-N`} className="cursor-pointer">No</Label>
            </div>
          </div>
        </RadioGroup>
      </div>
    );
  }

  if (item.type === 'choose2') {
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <RadioGroup value={value} onValueChange={onChange}>
          <div className="space-y-3">
            <div className="flex items-start space-x-3 p-4 border-2 border-gray-200 rounded-lg hover:border-primary transition-colors cursor-pointer">
              <RadioGroupItem value="A" id={`${item.id}-A`} className="mt-1" />
              <Label htmlFor={`${item.id}-A`} className="cursor-pointer flex-1">
                <span className="font-semibold text-primary">A:</span> {item.optionA_text}
              </Label>
            </div>
            <div className="flex items-start space-x-3 p-4 border-2 border-gray-200 rounded-lg hover:border-primary transition-colors cursor-pointer">
              <RadioGroupItem value="B" id={`${item.id}-B`} className="mt-1" />
              <Label htmlFor={`${item.id}-B`} className="cursor-pointer flex-1">
                <span className="font-semibold text-primary">B:</span> {item.optionB_text}
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>
    );
  }

  return null;
}

