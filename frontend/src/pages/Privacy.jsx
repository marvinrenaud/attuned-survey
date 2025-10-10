import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

export default function Privacy() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <Button
          variant="ghost"
          onClick={() => navigate('/')}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Home
        </Button>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">Privacy Policy</h1>
          
          <div className="prose prose-gray max-w-none space-y-6">
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Data Collection</h2>
              <p className="text-gray-700">
                Attuned collects only the information you provide through the survey, including your name 
                and your responses to intimacy-related questions. We do not collect email addresses, 
                phone numbers, or any other personally identifiable information beyond your name.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Data Storage</h2>
              <p className="text-gray-700">
                All survey responses are stored locally in your browser using LocalStorage. Your data 
                never leaves your device and is not transmitted to any external servers. This means:
              </p>
              <ul className="list-disc list-inside text-gray-700 ml-4 space-y-2">
                <li>Your responses are private and accessible only on this device</li>
                <li>Clearing your browser data will delete all stored responses</li>
                <li>No cloud backup or synchronization occurs</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Data Usage</h2>
              <p className="text-gray-700">
                Your survey responses are used solely to calculate your intimacy profile, including 
                your archetype, dial scores, and compatibility matching (if a baseline is set). 
                No analytics, tracking, or third-party services have access to your responses.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Data Sharing</h2>
              <p className="text-gray-700">
                We do not share, sell, or transmit your data to any third parties. Your responses 
                remain on your device and are never uploaded to external servers.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Admin Access</h2>
              <p className="text-gray-700">
                The admin panel (password-protected) allows viewing all submissions stored locally 
                on the device. This is intended for research or validation purposes within a controlled 
                environment. Admin access does not transmit data externally.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Your Rights</h2>
              <p className="text-gray-700">
                You have full control over your data:
              </p>
              <ul className="list-disc list-inside text-gray-700 ml-4 space-y-2">
                <li>You can edit your responses at any time from the results page</li>
                <li>You can clear all data by clearing your browser's LocalStorage</li>
                <li>You can export your data as JSON or CSV from the admin panel</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Security</h2>
              <p className="text-gray-700">
                Since all data is stored locally, security depends on your device and browser security. 
                We recommend using a secure, up-to-date browser and protecting your device with a password.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Changes to This Policy</h2>
              <p className="text-gray-700">
                We may update this privacy policy as the application evolves. Any changes will be 
                reflected on this page with an updated revision date.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-3">Contact</h2>
              <p className="text-gray-700">
                This is a prototype application built for validation purposes. For questions or concerns, 
                please contact the development team.
              </p>
            </section>

            <p className="text-sm text-gray-500 mt-8">
              Last updated: October 2025
            </p>
          </div>
        </div>

        <footer className="text-center mt-8 text-sm text-gray-500">
          <p>Made with ♥️ in BK</p>
        </footer>
      </div>
    </div>
  );
}

