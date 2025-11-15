import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Users,
  Calendar,
  Lightbulb,
  Target,
  MessageSquare,
  Sparkles
} from 'lucide-react'
import './LandingPage.css'

export default function LandingPage() {
  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <div className="landing-header-container">
          <div className="landing-logo">CTLChat</div>
          <nav className="landing-nav">
            <a href="#features">Features</a>
            <a href="#examples">Examples</a>
          </nav>
          <Link to="/login">
            <Button>Get Started</Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-badge">AI-Powered Team Building & Planning</div>

        <h1 className="hero-title">
          Plan exceptional team building programs with AI
        </h1>

        <p className="hero-description">
          Design engaging team activities, create comprehensive program schedules, and collaborate with your team using AI. Transform team building from a challenge into a streamlined, creative process.
        </p>

        <div className="hero-ctas">
          <Link to="/login">
            <Button size="lg">Start Planning</Button>
          </Link>
        </div>

        {/* Hero Image */}
        <div className="hero-image-container">
          <img
            src="/program_query.png"
            alt="CTLChat Team Planning Dashboard"
            className="hero-image"
          />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="features-container">
          <div className="section-header">
            <h2 className="section-title">Built for team leaders and HR professionals</h2>
            <p className="section-description">
              Everything you need to plan, organize, and execute memorable team building programs
            </p>
          </div>

          <div className="features-grid">
            <FeatureCard
              icon={<Sparkles className="w-6 h-6" />}
              title="AI Program Assistant"
              description="Get intelligent suggestions for team activities, icebreakers, and program structures based on your team's size, goals, and preferences."
            />

            <FeatureCard
              icon={<Calendar className="w-6 h-6" />}
              title="Smart Scheduling"
              description="Create detailed program timelines with AI assistance. Optimize session lengths, breaks, and activity sequences for maximum engagement."
            />

            <FeatureCard
              icon={<Users className="w-6 h-6" />}
              title="Team Collaboration"
              description="Work together with your planning team in real-time. Share ideas, get feedback, and refine programs collaboratively."
            />

            <FeatureCard
              icon={<Target className="w-6 h-6" />}
              title="Goal-Oriented Planning"
              description="Define your team building objectives and let AI recommend activities that align with your goals, whether it's communication, leadership, or trust-building."
            />

            <FeatureCard
              icon={<MessageSquare className="w-6 h-6" />}
              title="Interactive Planning Chat"
              description="Chat with AI to brainstorm ideas, refine concepts, and get instant answers to your team building questions."
            />

            <FeatureCard
              icon={<Lightbulb className="w-6 h-6" />}
              title="Creative Ideas Library"
              description="Access a vast repository of team building activities, games, and exercises. Get fresh ideas tailored to your specific needs."
            />
          </div>
        </div>
      </section>

      {/* Example Section */}
      <section id="examples" className="example-section">
        <div className="example-grid">
          <div>
            <h2 className="example-title">From idea to execution in minutes</h2>

            <p className="example-text">
              Stop struggling with blank pages and generic templates. Chat with our AI about your team's needs, and watch as it helps you craft a personalized program.
            </p>

            <p className="example-text">
              Whether you're planning a half-day workshop, a weekend retreat, or a full week of activities, CTLChat understands your goals and provides actionable recommendations.
            </p>

          </div>

          {/* Example Image */}
          <div className="hero-image-container">
            <img
              src="/icebreaker_query.png"
              alt="Example planning conversation"
              className="hero-image"
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-container">
          <h2 className="cta-title">Transform your team building programs</h2>
          <p className="cta-description">
            See how CTLChat can help you plan engaging, meaningful team experiences with the power of AI.
          </p>
          <Link to="/login">
            <Button size="lg">Start Planning</Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        &copy; 2025 CTLChat. All rights reserved.
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="feature-card">
      <div className="feature-icon">
        {icon}
      </div>
      <h3 className="feature-title">{title}</h3>
      <p className="feature-description">{description}</p>
    </div>
  )
}
