import { Link } from 'react-router-dom';
import { ArrowRight, Sparkles, Zap, Shield, Download } from 'lucide-react';
import FloatingParticles from '../components/shared/FloatingParticles';

const LandingPage = () => {
  return (
    <div className="min-h-screen relative">
      <FloatingParticles />
      
      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 relative z-10">
        <div className="max-w-6xl mx-auto text-center">
          <div className="animate-fade-in">
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Transform Your Career with{' '}
              <span className="gradient-text">AI-Powered CVs</span>
            </h1>
            <p className="text-xl md:text-2xl text-white/80 mb-8 max-w-3xl mx-auto leading-relaxed">
              Create stunning, professional resumes that stand out from the crowd. 
              Our AI technology adapts your CV to any job requirements in seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/app">
                <button className="gradient-button text-black font-semibold px-8 py-4 rounded-full flex items-center space-x-2 text-lg">
                  <span>Start Creating</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
              </Link>
              <Link to="/login">
                <button className="glass-effect text-white font-semibold px-8 py-4 rounded-full hover:bg-white/10 transition-all duration-300 text-lg">
                  Sign In
                </button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16 animate-fade-in">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Why Choose <span className="gradient-text">MorphCV</span>?
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Experience the future of resume creation with our cutting-edge features
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Sparkles,
                title: 'AI-Powered Generation',
                description: 'Our advanced AI analyzes job descriptions and crafts perfect CVs tailored to each opportunity.',
              },
              {
                icon: Zap,
                title: 'Lightning Fast',
                description: 'Generate professional resumes in seconds, not hours. Save time and apply to more positions.',
              },
              {
                icon: Shield,
                title: 'ATS Optimized',
                description: 'Ensure your CV passes through Applicant Tracking Systems with our optimized formatting.',
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="glass-effect p-8 rounded-2xl hover:bg-white/10 transition-all duration-300 animate-slide-in"
                style={{ animationDelay: `${index * 0.2}s` }}
              >
                <div className="gradient-border rounded-full w-16 h-16 flex items-center justify-center mb-6">
                  <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-full w-14 h-14 flex items-center justify-center">
                    <feature.icon className="w-8 h-8 text-white" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold mb-4 text-white">{feature.title}</h3>
                <p className="text-white/80 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Simple <span className="gradient-text">Three-Step</span> Process
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              From information to interview-ready CV in minutes
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Input Your Details',
                description: 'Fill in your personal information, experience, skills, and education in our intuitive form.',
              },
              {
                step: '02',
                title: 'AI Magic Happens',
                description: 'Our AI analyzes your information and generates a professional, tailored CV instantly.',
              },
              {
                step: '03',
                title: 'Download & Apply',
                description: 'Get your polished CV in multiple formats and start applying to your dream jobs.',
              },
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="gradient-text text-6xl font-bold mb-4">{step.step}</div>
                <div className="glass-effect p-6 rounded-2xl">
                  <h3 className="text-xl font-bold mb-3 text-white">{step.title}</h3>
                  <p className="text-white/80">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 relative z-10">
        <div className="max-w-4xl mx-auto text-center">
          <div className="glass-effect p-12 rounded-3xl">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Ready to <span className="gradient-text">Transform</span> Your Career?
            </h2>
            <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
              Join thousands of professionals who've already boosted their career prospects with MorphCV
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/app">
                <button className="gradient-button text-black font-semibold px-8 py-4 rounded-full flex items-center space-x-2 text-lg">
                  <Download className="w-5 h-5" />
                  <span>Create Your CV Now</span>
                </button>
              </Link>
            </div>
            <p className="text-sm text-white/60 mt-4">
              No credit card required • Free forever plan available
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-white/10 relative z-10">
        <div className="max-w-6xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="w-8 h-8 gradient-button rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-black" />
            </div>
            <span className="text-xl font-bold gradient-text">MorphCV</span>
          </div>
          <p className="text-white/60">
            © 2025 MorphCV. All rights reserved. • Privacy Policy • Terms of Service
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
