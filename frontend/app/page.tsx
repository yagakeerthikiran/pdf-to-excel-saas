export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="hero-section min-h-screen flex items-center justify-center text-white">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6">
            PDF to Excel
            <span className="block text-yellow-300">Made Simple</span>
          </h1>
          
          <p className="text-xl md:text-2xl mb-8 max-w-2xl mx-auto text-gray-200">
            Transform your PDF documents into editable Excel spreadsheets 
            with our AI-powered conversion tool. Fast, accurate, and secure.
          </p>
          
          <div className="space-y-4 sm:space-y-0 sm:space-x-4 sm:flex sm:justify-center">
            <button className="btn-primary w-full sm:w-auto">
              Start Converting Now
            </button>
            <button className="btn-secondary w-full sm:w-auto bg-white text-gray-800 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
              View Pricing
            </button>
          </div>
          
          <div className="mt-12 card p-6 max-w-md mx-auto">
            <h3 className="text-lg font-semibold mb-2">🚀 Coming Soon to Australia</h3>
            <p className="text-gray-200 text-sm">
              Professional PDF to Excel conversion service launching soon. 
              Built for Australian businesses.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-800 mb-4">
              Why Choose Our Service?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              Built with enterprise-grade security and powered by advanced AI 
              for the most accurate conversions.
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
              <p className="text-gray-600">
                Convert PDFs to Excel in seconds with our optimized processing engine.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🛡️</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">Secure & Private</h3>
              <p className="text-gray-600">
                Your documents are processed securely and deleted within 24 hours.
              </p>
            </div>
            
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-xl font-semibold mb-2">AI-Powered Accuracy</h3>
              <p className="text-gray-600">
                Advanced AI ensures accurate table detection and data extraction.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-8">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2024 PDF to Excel SaaS. Built for Australian businesses.</p>
          <p className="text-gray-400 text-sm mt-2">
            Backend API: Ready | Frontend: Coming Soon
          </p>
        </div>
      </footer>
    </div>
  )
}