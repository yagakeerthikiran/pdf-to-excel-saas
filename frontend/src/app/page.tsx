import Link from "next/link";

const DebuggingInfo = () => {
  return (
    <div style={{
      backgroundColor: '#111',
      color: '#eee',
      padding: '20px',
      border: '2px solid red',
      margin: '20px',
      fontFamily: 'monospace',
      fontSize: '14px',
      whiteSpace: 'pre-wrap',
      zIndex: 9999,
      position: 'relative',
    }}>
      <h2 style={{ color: 'red', marginBottom: '10px' }}>--- JULES'S DEBUGGING PANEL ---</h2>
      <p>This is a temporary panel to verify environment variables. It will be removed once the issue is fixed.</p>
      <hr style={{ margin: '10px 0' }} />
      <p><strong>NEXT_PUBLIC_SUPABASE_URL:</strong> "{process.env.NEXT_PUBLIC_SUPABASE_URL}"</p>
      <p><strong>NEXT_PUBLIC_SUPABASE_ANON_KEY:</strong> "{process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}"</p>
      <p><strong>NEXT_PUBLIC_BACKEND_URL:</strong> "{process.env.NEXT_PUBLIC_BACKEND_URL}"</p>
      <hr style={{ margin: '10px 0' }} />
      <p><strong>Instructions:</strong> Please compare these values character-for-character with the values in your Supabase dashboard and AWS Load Balancer URL. Check for typos, extra spaces, or missing characters.</p>
    </div>
  );
};


export default function HomePage() {
  return (
    <div className="min-h-screen">
      <DebuggingInfo />
      {/* Navigation */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">PDF to Excel</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link 
                href="/pricing" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Pricing
              </Link>
              <Link 
                href="/auth/signin" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
              >
                Sign In
              </Link>
              <Link 
                href="/auth/signup" 
                className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-700 min-h-screen flex items-center justify-center text-white">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            PDF to Excel
            <span className="block text-yellow-300">Made Simple</span>
          </h1>
          
          <p className="text-xl md:text-2xl mb-8 max-w-2xl mx-auto text-gray-200">
            Transform your PDF documents into editable Excel spreadsheets 
            with our AI-powered conversion tool. Fast, accurate, and secure.
          </p>
          
          <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <Link 
              href="/auth/signup"
              className="inline-block bg-yellow-400 text-gray-900 px-8 py-4 rounded-lg font-semibold hover:bg-yellow-300 transition-colors text-lg"
            >
              Start Converting Now
            </Link>
            <Link 
              href="/pricing"
              className="inline-block bg-white text-gray-800 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition-colors text-lg"
            >
              View Pricing
            </Link>
          </div>
          
          <div className="mt-12 bg-white/10 backdrop-blur-sm rounded-lg p-6 max-w-md mx-auto">
            <h3 className="text-lg font-semibold mb-2">🚀 Now Live in Australia</h3>
            <p className="text-gray-200 text-sm">
              Professional PDF to Excel conversion service. 
              Built for Australian businesses with local data processing.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Why Choose Our Service?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Built with enterprise-grade security and powered by advanced AI 
              for the most accurate conversions available today.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center p-8">
              <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">⚡</span>
              </div>
              <h3 className="text-2xl font-semibold mb-4">Lightning Fast</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Convert PDFs to Excel in seconds with our optimized processing engine.
                No waiting around for results.
              </p>
            </div>
            
            <div className="text-center p-8">
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">🛡️</span>
              </div>
              <h3 className="text-2xl font-semibold mb-4">Secure & Private</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Your documents are processed securely in Australia and automatically 
                deleted within 24 hours.
              </p>
            </div>
            
            <div className="text-center p-8">
              <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">🎯</span>
              </div>
              <h3 className="text-2xl font-semibold mb-4">AI-Powered Accuracy</h3>
              <p className="text-gray-600 text-lg leading-relaxed">
                Advanced AI ensures accurate table detection and data extraction, 
                even from complex layouts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">95%+</div>
              <div className="text-lg text-gray-600">Conversion Accuracy</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">&lt;30s</div>
              <div className="text-lg text-gray-600">Average Processing Time</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-blue-600 mb-2">24hrs</div>
              <div className="text-lg text-gray-600">Automatic File Deletion</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-blue-600 text-white">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Convert Your PDFs?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of users who trust us with their document conversion needs.
            Start with 5 free conversions, no credit card required.
          </p>
          <div className="space-x-4">
            <Link 
              href="/auth/signup"
              className="inline-block bg-yellow-400 text-gray-900 px-8 py-4 rounded-lg font-semibold hover:bg-yellow-300 transition-colors text-lg"
            >
              Start Free Trial
            </Link>
            <Link 
              href="/pricing"
              className="inline-block bg-blue-700 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-800 transition-colors border border-blue-400 text-lg"
            >
              View All Plans
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="md:col-span-2">
              <h3 className="text-2xl font-bold mb-4">PDF to Excel</h3>
              <p className="text-gray-400 mb-4">
                Professional PDF to Excel conversion service built for Australian businesses. 
                Fast, accurate, and secure document processing.
              </p>
              <p className="text-sm text-gray-500">
                Made in Australia 🇦🇺 • Hosted in Sydney
              </p>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-gray-400">
                <li><Link href="/pricing" className="hover:text-white">Pricing</Link></li>
                <li><Link href="/dashboard" className="hover:text-white">Dashboard</Link></li>
                <li><a href="#" className="hover:text-white">API Docs</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="text-lg font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Help Center</a></li>
                <li><a href="#" className="hover:text-white">Contact Us</a></li>
                <li><a href="#" className="hover:text-white">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-12 pt-8 text-center">
            <p className="text-gray-400">
              &copy; 2024 PDF to Excel SaaS. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
