import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { SegmentedControl } from '@/components/ui/segmented-control';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react';
import { getSurveyChapters, validateChapter, getSchema } from '../lib/surveyData';
import { calculateProfile } from '../lib/scoring/profileCalculator';
import { saveSubmission, saveCurrentSession, getCurrentSession, clearCurrentSession } from '../lib/storage/apiStore';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

const DEBUG_SURVEY = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('debug') === '1';
function sdbg(...args) {
  if (DEBUG_SURVEY) console.log('[SURVEY DEBUG]', ...args);
}

const ANATOMY_OPTIONS = [
  { value: 'penis', label: 'Penis' },
  { value: 'vagina', label: 'Vagina' },
  { value: 'breasts', label: 'Breasts' }
];

export default function Survey() {
  const navigate = useNavigate();
  const [chapters] = useState(getSurveyChapters());
  try {
    const chaptersForLog = getSurveyChapters();
    const flat = [];
    for (const ch of chaptersForLog) {
      for (const it of (ch?.items || [])) {
        flat.push({ chapter: ch?.title || ch?.name, id: it?.id, type: it?.type, text: it?.text });
      }
    }
    sdbg('RENDER_ORDER', flat.length, 'items');
    console.table(flat.slice(0, 200));
  } catch (e) {
    sdbg('Failed to log render order', e);
  }
  const [currentChapterIndex, setCurrentChapterIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [name, setName] = useState('');
  const [anatomySelf, setAnatomySelf] = useState([]);
  const [anatomyPreference, setAnatomyPreference] = useState([]);
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
      setAnatomySelf(session.anatomySelf || []);
      setAnatomyPreference(session.anatomyPreference || []);
      const hasDemographics = Boolean(
        (session.name && session.name.trim()) && 
        session.anatomySelf && session.anatomySelf.length > 0 &&
        session.anatomyPreference && session.anatomyPreference.length > 0
      );
      setShowNameInput(!hasDemographics);
    }
  }, []);

  // Save session on changes
  useEffect(() => {
    if (name || anatomySelf.length > 0 || anatomyPreference.length > 0 || Object.keys(answers).length > 0) {
      saveCurrentSession({
        answers,
        currentChapter: currentChapterIndex,
        name,
        anatomySelf,
        anatomyPreference
      });
    }
  }, [answers, currentChapterIndex, name, anatomySelf, anatomyPreference]);

  const handleAnswer = (itemId, value) => {
    setAnswers(prev => ({
      ...prev,
      [itemId]: value
    }));
    setErrors([]);
  };

  const handleNameSubmit = () => {
    const validationErrors = [];
    if (!name.trim()) {
      validationErrors.push('Please enter your name to continue');
    }
    if (!anatomySelf || anatomySelf.length === 0) {
      validationErrors.push('Please select at least one option for what anatomy you have');
    }
    if (!anatomyPreference || anatomyPreference.length === 0) {
      validationErrors.push('Please select at least one option for what anatomy you like to play with');
    }

    if (validationErrors.length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors([]);
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
      
      // Calculate profile using v0.4 calculator
      const uniqueId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      console.log('Calculating v0.4 profile...');
      
      // Add anatomy answers to survey answers (D1, D2)
      const answersWithAnatomy = {
        ...answers,
        D1: anatomySelf,
        D2: anatomyPreference
      };
      
      const profile = calculateProfile(uniqueId, answersWithAnatomy);
      console.log('Profile calculated:', {
        arousal: profile.arousal_propensity,
        power: profile.power_dynamic.orientation,
        domains: profile.domain_scores,
        anatomy: profile.anatomy
      });
      
      const submission = {
        id: uniqueId,
        name,
        createdAt: new Date().toISOString(),
        answers: answersWithAnatomy,
        derived: profile
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
          <div className="space-y-6">
            <div>
              <Label htmlFor="name">Your Name</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  setErrors([]);
                }}
                placeholder="Enter your name"
                className="mt-1"
                onKeyPress={(e) => e.key === 'Enter' && handleNameSubmit()}
              />
            </div>
            
            <div>
              <Label className="text-base font-semibold">What anatomy do you have to play with?</Label>
              <p className="text-sm text-text-secondary mb-3">Select all that apply</p>
              <div className="space-y-2">
                {ANATOMY_OPTIONS.map(option => (
                  <div key={option.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`anatomy-self-${option.value}`}
                      checked={anatomySelf.includes(option.value)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setAnatomySelf(prev => [...prev, option.value]);
                        } else {
                          setAnatomySelf(prev => prev.filter(v => v !== option.value));
                        }
                        setErrors([]);
                      }}
                    />
                    <label
                      htmlFor={`anatomy-self-${option.value}`}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      {option.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <Label className="text-base font-semibold">What anatomy do you like to play with in partners?</Label>
              <p className="text-sm text-text-secondary mb-3">Select all that apply</p>
              <div className="space-y-2">
                {ANATOMY_OPTIONS.map(option => (
                  <div key={option.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`anatomy-pref-${option.value}`}
                      checked={anatomyPreference.includes(option.value)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setAnatomyPreference(prev => [...prev, option.value]);
                        } else {
                          setAnatomyPreference(prev => prev.filter(v => v !== option.value));
                        }
                        setErrors([]);
                      }}
                    />
                    <label
                      htmlFor={`anatomy-pref-${option.value}`}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                    >
                      {option.label}
                    </label>
                  </div>
                ))}
              </div>
            </div>
            {errors.length > 0 && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <ul className="list-disc list-inside space-y-1">
                    {errors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </AlertDescription>
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
    const likertOptions = [1, 2, 3, 4, 5, 6, 7].map(num => ({
      value: num.toString(),
      label: num.toString()
    }));

    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <SegmentedControl
          options={likertOptions}
          value={value?.toString()}
          onValueChange={(v) => onChange(Number(v))}
          name={`${item.id}`}
          data-testid={`likert-${item.id}`}
        />
        <div className="flex justify-between text-xs text-text-secondary mt-2">
          <span>Strongly Disagree</span>
          <span>Neutral</span>
          <span>Strongly Agree</span>
        </div>
      </div>
    );
  }

  if (item.type === 'ymn' || item.type === 'chooseYMN') {
    const ymnOptions = [
      { value: 'Y', label: 'Yes' },
      { value: 'M', label: 'Maybe' },
      { value: 'N', label: 'No' }
    ];

    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <SegmentedControl
          options={ymnOptions}
          value={value}
          onValueChange={onChange}
          name={`${item.id}`}
          data-testid={`ymn-${item.id}`}
        />
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

  if (item.type === 'checklist') {
    // C1: Hard boundaries checklist (8-key taxonomy)
    const options = [
      { value: 'hardBoundaryImpact', label: 'Impact play' },
      { value: 'hardBoundaryRestrain', label: 'Bondage and Restraints' },
      { value: 'hardBoundaryBreath', label: 'Breath Play' },
      { value: 'hardBoundaryDegrade', label: 'Degradation' },
      { value: 'hardBoundaryPublic', label: 'Public Play' },
      { value: 'hardBoundaryRecord', label: 'Recording' },
      { value: 'hardBoundaryAnal', label: 'Anal' },
      { value: 'hardBoundaryWatersports', label: 'Watersports / scat play' }
    ];
    
    const selected = Array.isArray(value) ? value : (value ? value.split(',').map(s => s.trim()) : []);
    
    const handleToggle = (option) => {
      const newSelected = selected.includes(option)
        ? selected.filter(s => s !== option)
        : [...selected, option];
      onChange(newSelected); // Pass array directly
    };

    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <p className="text-sm text-text-secondary mb-4">
          Select all activities that are hard boundaries for you (absolutely not interested).
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {options.map((option) => (
            <div key={option.value} className="flex items-center space-x-2">
              <Checkbox
                id={`${item.id}-${option.value}`}
                checked={selected.includes(option.value)}
                onCheckedChange={() => handleToggle(option.value)}
              />
              <Label htmlFor={`${item.id}-${option.value}`} className="cursor-pointer">
                {option.label}
              </Label>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (item.type === 'text') {
    // C2: Additional notes
    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <Textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Enter any specific boundaries or concerns..."
          className="min-h-[100px]"
        />
      </div>
    );
  }

  if (item.type === 'boundary') {
    // Legacy boundary type - simple yes/no
    const boundaryOptions = [
      { value: 'Y', label: 'Yes' },
      { value: 'N', label: 'No' }
    ];

    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <SegmentedControl
          options={boundaryOptions}
          value={value}
          onValueChange={onChange}
          name={`${item.id}`}
          data-testid={`boundary-${item.id}`}
        />
      </div>
    );
  }

  if (item.type === 'choose2') {
    const choose2Options = [
      { value: 'A', label: `A: ${item.optionA_text}` },
      { value: 'B', label: `B: ${item.optionB_text}` }
    ];

    return (
      <div data-testid={`item-${item.id}`}>
        <Label className="text-base font-medium text-text-primary mb-3 block">
          {item.text}
        </Label>
        <div className="space-y-3">
          {choose2Options.map((option) => (
            <div 
              key={option.value}
              className={`p-4 border-2 rounded-lg transition-colors cursor-pointer ${
                value === option.value 
                  ? 'border-primary bg-primary/5' 
                  : 'border-gray-200 hover:border-primary'
              }`}
              onClick={() => onChange(option.value)}
            >
              <div className="flex items-start space-x-3">
                <div className={`w-4 h-4 rounded-full border-2 mt-1 flex items-center justify-center ${
                  value === option.value 
                    ? 'border-primary bg-primary' 
                    : 'border-gray-300'
                }`}>
                  {value === option.value && (
                    <div className="w-2 h-2 rounded-full bg-white"></div>
                  )}
                </div>
                <Label className="cursor-pointer flex-1">
                  <span className="font-semibold text-primary">{option.value}:</span> {option.label.split(': ')[1]}
                </Label>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return null;
}

