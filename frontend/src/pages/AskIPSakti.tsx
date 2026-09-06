import React, { useState } from 'react'
import { Send, ChevronDown, ChevronUp } from 'lucide-react'

interface RetrievedChunk {
  id: string
  text: string
  metadata: {
    document_name: string
    page_num: string
    chunk_id: string
    chunk_index: string
  }
  distance: number
  relevance_score: number
}

interface QueryResponse {
  answer: string
  retrieved_chunks: RetrievedChunk[]
  has_sufficient_evidence: boolean
  confidence_score: number
  rag_process?: {
    question: string
    retrieval_count: number
    top_chunks: Array<{
      text: string
      document: string
      page: string
      relevance: number
    }>
    context_length: number
    llm_model: string
  }
}

interface ProductProfileForm {
  product_type: string
  ingredients: string
  proportions: string
  intended_use: string
  target_application: string
  preparation_method: string
  claimed_effect: string
}

interface ProductAnalysisResponse {
  product_profile: Omit<ProductProfileForm, 'ingredients'> & { ingredients: string[] }
  status: string
}

const AskIPSakti = () => {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [mode, setMode] = useState<'question' | 'product'>('question')
  const [productLoading, setProductLoading] = useState(false)
  const [productResponse, setProductResponse] = useState<ProductAnalysisResponse | null>(null)
  const [productProfile, setProductProfile] = useState<ProductProfileForm>({
    product_type: '',
    ingredients: '',
    proportions: '',
    intended_use: '',
    target_application: '',
    preparation_method: '',
    claimed_effect: ''
  })
  const [showRAGProcess, setShowRAGProcess] = useState(false)
  const [showEvidence, setShowEvidence] = useState(true)
  const [jurisdiction, setJurisdiction] = useState<'india' | 'international'>('india')
  const [ipRegime, setIpRegime] = useState<string>('all')

  const indiaQuestions = [
    "Can traditional Ayurvedic knowledge be patented?",
    "What is Section 3(p) of the Patents Act?",
    "What is the Traditional Knowledge Digital Library (TKDL)?",
    "How does the Biological Diversity Act affect Ayurveda?",
    "What is the difference between classical and proprietary Ayurvedic medicines?",
    "What are the ABS requirements for Ayurvedic products?",
    "What is the patentability of Ayurvedic formulations under Indian law?",
    "How do I file for a Geographical Indication for Ayurvedic products?"
  ]

  const internationalQuestions = [
    "What is TRIPS and how does it affect traditional knowledge?",
    "What is the Nagoya Protocol on Access and Benefit-Sharing?",
    "How does the WIPO GRATK Treaty protect genetic resources?",
    "What are the international IP protections for traditional medicine?",
    "How can I protect Ayurvedic knowledge under the PCT system?",
    "What is the CBD's stance on traditional knowledge protection?",
    "How do international treaties address biopiracy?",
    "What are the export market IP requirements for Ayurvedic products?"
  ]

  const suggestedQuestions = jurisdiction === 'india' ? indiaQuestions : internationalQuestions

  const legalFrameworks = {
    india: [
      { name: 'Patents Act, 1970', type: 'Statute', description: 'Primary legislation governing patents in India' },
      { name: 'Patents Rules, 2024', type: 'Rules', description: 'Updated rules for patent application and prosecution' },
      { name: 'Biological Diversity Act, 2002 (amended 2023)', type: 'Statute', description: 'Regulates access to biological resources and benefit-sharing' },
      { name: 'Biodiversity Rules, 2024', type: 'Rules', description: 'Implementation rules for ABS compliance' },
      { name: 'Drugs and Cosmetics Act, 1940', type: 'Statute', description: 'Regulates Ayurvedic drug manufacturing and marketing' },
      { name: 'Geographical Indications of Goods Act, 1999', type: 'Statute', description: 'Protection for geographical indications' },
      { name: 'Trade Marks Act, 1999', type: 'Statute', description: 'Trademark registration and protection' },
      { name: 'Plant Varieties Protection and Farmers Rights Act, 2001', type: 'Statute', description: 'Protection for plant varieties' }
    ],
    international: [
      { name: 'TRIPS Agreement', type: 'Treaty', description: 'WTO agreement on trade-related IP rights' },
      { name: 'Convention on Biological Diversity (CBD)', type: 'Treaty', description: 'International framework for biodiversity conservation' },
      { name: 'Nagoya Protocol', type: 'Protocol', description: 'Access and benefit-sharing for genetic resources' },
      { name: 'WIPO GRATK Treaty (2024)', type: 'Treaty', description: 'Genetic resources and associated traditional knowledge' },
      { name: 'PCT (Patent Cooperation Treaty)', type: 'Treaty', description: 'International patent filing system' },
      { name: 'Madrid System', type: 'System', description: 'International trademark registration' },
      { name: 'Hague System', type: 'System', description: 'International industrial design registration' },
      { name: 'Budapest Treaty', type: 'Treaty', description: 'Microorganism deposit for patent purposes' }
    ]
  }

  const ipRegimes = [
    { value: 'all', label: 'All IP Regimes' },
    { value: 'patents', label: 'Patents' },
    { value: 'gi', label: 'Geographical Indications' },
    { value: 'trademarks', label: 'Trademarks' },
    { value: 'copyright', label: 'Copyright' },
    { value: 'designs', label: 'Designs' },
    { value: 'trade_secrets', label: 'Trade Secrets' },
    { value: 'plant_variety', label: 'Plant Variety Rights' },
    { value: 'abs', label: 'ABS & Biodiversity' }
  ]

  const regimeGuidance = {
    patents: {
      keySections: ['Section 3(p) - TK exclusion', 'Section 3(d) - Incremental innovation', 'Section 3(k) - Software/Algorithms'],
      keyForms: ['Form 1 - Application', 'Form 2 - Complete Specification', 'Form 3 - Statement and Undertaking'],
      timeline: '12-18 months for examination, 20 years term',
      ayurvedaRelevance: 'Classical formulations face Section 3(p) bar; novel formulations may be patentable'
    },
    gi: {
      keySections: ['Section 2(f) - GI definition', 'Section 8 - Registration', 'Section 10 - Infringement'],
      keyForms: ['Form GI-1 - Application', 'Form GI-2 - Statement of Case'],
      timeline: '12-24 months for registration, indefinite term (renewable every 10 years)',
      ayurvedaRelevance: 'Protects Ayurvedic products with geographical origin (e.g., "Kashmir Saffron")'
    },
    trademarks: {
      keySections: ['Section 9 - Absolute grounds for refusal', 'Section 11 - Infringement', 'Section 34 - Defence of honest concurrent use'],
      keyForms: ['TM-A - Application', 'TM-1 - Classification'],
      timeline: '18-30 months for registration, 10 years term (renewable)',
      ayurvedaRelevance: 'Brand names, logos, and packaging can be trademarked'
    },
    copyright: {
      keySections: ['Section 13 - Works protected', 'Section 17 - Authorship', 'Section 51 - Infringement'],
      keyForms: ['Form XIV - Application for Registration'],
      timeline: 'Registration in 2-3 months, lifetime + 60 years',
      ayurvedaRelevance: 'Protects textual compilations, formulations documentation, and creative works'
    },
    designs: {
      keySections: ['Section 2(d) - Design definition', 'Section 4 - Novelty', 'Section 22 - Term'],
      keyForms: ['Form 1 - Application', 'Form 2 - Representation of Design'],
      timeline: '6-12 months for registration, 10 years term (renewable to 15 years)',
      ayurvedaRelevance: 'Protects ornamental design of Ayurvedic product packaging'
    },
    trade_secrets: {
      keySections: ['Common law protection', 'Contractual safeguards'],
      keyForms: ['NDA agreements', 'Employment contracts'],
      timeline: 'Indefinite (as long as secret is maintained)',
      ayurvedaRelevance: 'Protects proprietary formulations and manufacturing processes'
    },
    plant_variety: {
      keySections: ['Section 14 - Breeders Rights', 'Section 15 - Farmers Rights', 'Section 16 - Registration'],
      keyForms: ['Form I - Application', 'Form II - Technical Questionnaire'],
      timeline: '12-24 months for registration, 15-18 years term',
      ayurvedaRelevance: 'Protects new plant varieties used in Ayurvedic medicines'
    },
    abs: {
      keySections: ['Section 3 - Access to biological resources', 'Section 7 - Benefit Sharing', 'Section 24 - Offences'],
      keyForms: ['Form I - Access application', 'Form II - Benefit Sharing Agreement'],
      timeline: '3-6 months for approval, ongoing compliance',
      ayurvedaRelevance: 'Mandatory for Ayurvedic products using biological resources from India'
    }
  }

  // Citation parser function
  const parseCitations = (text: string) => {
    const citationPatterns = [
      { pattern: /Section\s+(\d+[a-z]?)(?:\s*\([^)]+\))?/gi, type: 'section' },
      { pattern: /Rule\s+(\d+)/gi, type: 'rule' },
      { pattern: /Article\s+(\d+)/gi, type: 'article' },
      { pattern: /Clause\s+(\d+)/gi, type: 'clause' },
      { pattern: /Schedule\s+([A-Za-z]+)/gi, type: 'schedule' },
      { pattern: /Act\s+of\s+(\d{4})/gi, type: 'act' },
      { pattern: /Treaty/gi, type: 'treaty' },
      { pattern: /Protocol/gi, type: 'protocol' }
    ]

    const citations: Array<{ text: string; type: string }> = []
    let processedText = text

    citationPatterns.forEach(({ pattern, type }) => {
      const matches = text.match(pattern)
      if (matches) {
        matches.forEach(match => {
          citations.push({ text: match, type })
          processedText = processedText.replace(match, `<span class="bg-blue-100 text-blue-800 px-1 rounded font-medium">${match}</span>`)
        })
      }
    })

    return { processedText, citations }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setLoading(true)
    setResponse(null)

    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question, 
          show_rag_process: true,
          jurisdiction,
          ip_regime: ipRegime
        })
      })
      const data = await res.json()
      setResponse(data)
    } catch (error) {
      console.error('Error querying:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleProductSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setProductLoading(true)
    setProductResponse(null)

    try {
      const res = await fetch('http://localhost:8000/analyze-product', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...productProfile,
          ingredients: productProfile.ingredients
            .split(',')
            .map(ingredient => ingredient.trim())
            .filter(Boolean)
        })
      })

      if (!res.ok) {
        throw new Error(`Product analysis failed with status ${res.status}`)
      }

      setProductResponse(await res.json())
    } catch (error) {
      console.error('Error analyzing product:', error)
    } finally {
      setProductLoading(false)
    }
  }

  const updateProductField = (field: keyof ProductProfileForm, value: string) => {
    setProductProfile(prev => ({ ...prev, [field]: value }))
  }

  const generateFollowUpQuestions = (currentQuestion: string, retrievedChunks: RetrievedChunk[]) => {
    const followUpQuestions: string[] = []
    
    // Generate questions based on retrieved context
    const keywords = currentQuestion.toLowerCase().split(' ')
    
    if (keywords.some(k => k.includes('patent') || k.includes('protect'))) {
      followUpQuestions.push('What are the specific requirements for patenting Ayurvedic formulations?')
      followUpQuestions.push('How does Section 3(p) affect traditional knowledge patentability?')
    }
    
    if (keywords.some(k => k.includes('tkdl') || k.includes('traditional'))) {
      followUpQuestions.push('How do I search the TKDL for prior art?')
      followUpQuestions.push('What is the process for documenting traditional knowledge?')
    }
    
    if (keywords.some(k => k.includes('abs') || k.includes('biodiversity'))) {
      followUpQuestions.push('What forms are required for ABS compliance?')
      followUpQuestions.push('What are the penalties for non-compliance with ABS requirements?')
    }
    
    if (keywords.some(k => k.includes('gi') || k.includes('geographical'))) {
      followUpQuestions.push('What are the criteria for GI registration?')
      followUpQuestions.push('How long does GI registration take?')
    }
    
    // Add generic follow-ups if no specific ones generated
    if (followUpQuestions.length === 0) {
      followUpQuestions.push('What are the key legal frameworks governing this area?')
      followUpQuestions.push('What are the common challenges in this IP regime?')
    }
    
    return followUpQuestions.slice(0, 3)
  }

  const handleSuggestedQuestion = (q: string) => {
    setQuestion(q)
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deepBlue mb-2">Ask an IP Question</h1>
        <p className="text-gray-600">Ask about indexed IP documents or create a structured product profile for future analysis.</p>
      </div>

      <div className="mb-8 flex bg-white border border-lightGray rounded-lg p-1 w-fit">
        <button
          type="button"
          onClick={() => setMode('question')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'question' ? 'bg-deepBlue text-white' : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          Ask an IP Question
        </button>
        <button
          type="button"
          onClick={() => setMode('product')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            mode === 'product' ? 'bg-deepBlue text-white' : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          Analyze My Product
        </button>
      </div>

      {mode === 'product' ? (
        <div>
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-deepBlue mb-2">Product Profile</h2>
            <p className="text-gray-600">Record the characteristics that distinguish your product. This step only creates a structured profile.</p>
          </div>

          <form onSubmit={handleProductSubmit} className="bg-white border border-lightGray rounded-lg p-6 space-y-5">
            {([
              ['product_type', 'Product Type', 'e.g. Ayurvedic oil'],
              ['ingredients', 'Ingredients', 'e.g. Ashwagandha, Sesame Oil, Brahmi, Amla'],
              ['proportions', 'Proportions / Ratios', 'e.g. 20:10:30:40'],
              ['intended_use', 'Intended Use', 'e.g. Body massage'],
              ['target_application', 'Target Application', 'e.g. Muscles'],
              ['preparation_method', 'Preparation Method', 'Describe the heating or extraction process'],
              ['claimed_effect', 'Claimed Effect', 'e.g. Muscle relaxation']
            ] as const).map(([field, label, placeholder]) => (
              <label key={field} className="block">
                <span className="block text-sm font-medium text-gray-700 mb-2">{label}</span>
                {field === 'preparation_method' || field === 'claimed_effect' ? (
                  <textarea
                    required
                    value={productProfile[field]}
                    onChange={e => updateProductField(field, e.target.value)}
                    placeholder={placeholder}
                    rows={field === 'preparation_method' ? 3 : 2}
                    className="w-full p-3 border border-lightGray rounded-lg focus:outline-none focus:ring-2 focus:ring-deepBlue/20 resize-none"
                  />
                ) : (
                  <input
                    required
                    value={productProfile[field]}
                    onChange={e => updateProductField(field, e.target.value)}
                    placeholder={placeholder}
                    className="w-full p-3 border border-lightGray rounded-lg focus:outline-none focus:ring-2 focus:ring-deepBlue/20"
                  />
                )}
                {field === 'ingredients' && <span className="block text-xs text-gray-500 mt-1">Separate ingredients with commas.</span>}
              </label>
            ))}

            <button
              type="submit"
              disabled={productLoading}
              className="bg-deepBlue text-white px-5 py-3 rounded-lg hover:bg-blue-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {productLoading ? 'Creating Profile...' : 'Create Product Profile'}
            </button>
          </form>

          {productResponse && (
            <div className="mt-6 bg-white border border-lightGray rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-deepBlue">Structured Profile</h3>
                <span className="text-xs px-2 py-1 rounded-full bg-green-100 text-green-700">
                  {productResponse.status}
                </span>
              </div>
              <dl className="grid md:grid-cols-2 gap-4">
                {Object.entries(productResponse.product_profile).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 rounded-lg p-3">
                    <dt className="text-xs font-medium uppercase text-gray-500">{key.replace(/_/g, ' ')}</dt>
                    <dd className="text-sm text-gray-700 mt-1">{Array.isArray(value) ? value.join(', ') : value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
        </div>
      ) : (
      <div>

      {/* Jurisdiction & IP Regime Filters */}
      <div className="mb-6 flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Jurisdiction:</label>
          <div className="flex bg-white border border-lightGray rounded-lg overflow-hidden">
            <button
              type="button"
              onClick={() => setJurisdiction('india')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                jurisdiction === 'india'
                  ? 'bg-deepBlue text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              India
            </button>
            <button
              type="button"
              onClick={() => setJurisdiction('international')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                jurisdiction === 'international'
                  ? 'bg-deepBlue text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              International
            </button>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">IP Regime:</label>
          <select
            value={ipRegime}
            onChange={(e) => setIpRegime(e.target.value)}
            className="px-3 py-2 border border-lightGray rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-deepBlue/20"
          >
            {ipRegimes.map((regime) => (
              <option key={regime.value} value={regime.value}>
                {regime.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Legal Framework Display */}
      <div className="mb-8 bg-white border border-lightGray rounded-lg p-6">
        <h3 className="font-semibold text-deepBlue mb-4">
          Relevant Legal Frameworks ({jurisdiction === 'india' ? 'India' : 'International'})
        </h3>
        <div className="grid md:grid-cols-2 gap-3">
          {legalFrameworks[jurisdiction].map((framework, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-lg border border-lightGray">
              <div className="flex items-start justify-between mb-1">
                <span className="font-medium text-deepBlue text-sm">{framework.name}</span>
                <span className="text-xs px-2 py-0.5 bg-deepBlue/10 text-deepBlue rounded-full">
                  {framework.type}
                </span>
              </div>
              <p className="text-xs text-gray-600">{framework.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* IP Regime Guidance Card */}
      {ipRegime !== 'all' && regimeGuidance[ipRegime as keyof typeof regimeGuidance] && (
        <div className="mb-8 bg-white border border-lightGray rounded-lg p-6">
          <h3 className="font-semibold text-deepBlue mb-4">
            {ipRegimes.find(r => r.value === ipRegime)?.label} Guidance
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Sections</h4>
                <ul className="space-y-1">
                  {regimeGuidance[ipRegime as keyof typeof regimeGuidance].keySections.map((section, i) => (
                    <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                      <span className="text-saffron">•</span>
                      <span>{section}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Key Forms</h4>
                <ul className="space-y-1">
                  {regimeGuidance[ipRegime as keyof typeof regimeGuidance].keyForms.map((form, i) => (
                    <li key={i} className="text-xs text-gray-600 flex items-start gap-2">
                      <span className="text-saffron">•</span>
                      <span>{form}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Timeline</h4>
                <p className="text-xs text-gray-600">{regimeGuidance[ipRegime as keyof typeof regimeGuidance].timeline}</p>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Ayurveda Relevance</h4>
                <p className="text-xs text-gray-600">{regimeGuidance[ipRegime as keyof typeof regimeGuidance].ayurvedaRelevance}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Question Input */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask your Ayurveda IP question..."
            className="w-full p-4 border border-lightGray rounded-lg focus:outline-none focus:ring-2 focus:ring-deepBlue/20 resize-none"
            rows={3}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="absolute right-3 bottom-3 bg-deepBlue text-white px-4 py-2 rounded-lg hover:bg-blue-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            {loading ? 'Searching...' : 'Search Documents'}
          </button>
        </div>
        <p className="text-sm text-gray-500 mt-2">Press Enter to submit - Shift+Enter for new line</p>
      </form>

      {/* Suggested Questions */}
      {!response && !loading && (
        <div className="mb-8">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">SUGGESTED QUESTIONS</h3>
          <div className="grid md:grid-cols-2 gap-3">
            {suggestedQuestions.map((q, index) => (
              <button
                key={index}
                onClick={() => handleSuggestedQuestion(q)}
                className="text-left p-3 bg-white border border-lightGray rounded-lg hover:border-deepBlue hover:bg-deepBlue/5 transition-colors text-sm"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Response */}
      {response && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="bg-white border border-lightGray rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-deepBlue">Answer</h3>
                <p className="text-xs text-gray-500 mt-1">
                  Jurisdiction: <span className="font-medium capitalize">{jurisdiction}</span>
                  {ipRegime !== 'all' && ` | Regime: ${ipRegimes.find(r => r.value === ipRegime)?.label}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded-full ${
                  response.has_sufficient_evidence ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {response.has_sufficient_evidence ? 'Sufficient Evidence' : 'Limited Evidence'}
                </span>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  response.confidence_score >= 0.7 ? 'bg-blue-100 text-blue-700' : 
                  response.confidence_score >= 0.4 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                }`}>
                  Confidence: {(response.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div className="prose prose-sm max-w-none text-gray-700">
              <div 
                className="whitespace-pre-wrap"
                dangerouslySetInnerHTML={{ 
                  __html: parseCitations(response.answer).processedText 
                }}
              />
            </div>
          </div>

          {/* Show RAG Process Toggle */}
          {response.rag_process && (
            <div className="bg-white border border-lightGray rounded-lg">
              <button
                onClick={() => setShowRAGProcess(!showRAGProcess)}
                className="w-full p-4 flex items-center justify-between text-left"
              >
                <h3 className="font-semibold text-deepBlue">Show RAG Process</h3>
                {showRAGProcess ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
              </button>
              {showRAGProcess && (
                <div className="px-4 pb-4 border-t border-lightGray">
                  <div className="pt-4 space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-700">Question:</span>
                      <span className="text-gray-600">{response.rag_process.question}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-700">Retrieval:</span>
                      <span className="text-gray-600">{response.rag_process.retrieval_count} chunks retrieved</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-700">Context Length:</span>
                      <span className="text-gray-600">{response.rag_process.context_length} characters</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium text-gray-700">LLM Model:</span>
                      <span className="text-gray-600">{response.rag_process.llm_model}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Retrieved Evidence */}
          <div className="bg-white border border-lightGray rounded-lg">
            <button
              onClick={() => setShowEvidence(!showEvidence)}
              className="w-full p-4 flex items-center justify-between text-left"
            >
              <h3 className="font-semibold text-deepBlue">Retrieved Evidence ({response.retrieved_chunks.length} chunks)</h3>
              {showEvidence ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
            </button>
            {showEvidence && (
              <div className="px-4 pb-4 border-t border-lightGray">
                <div className="pt-4 space-y-4">
                  {response.retrieved_chunks.map((chunk, index) => (
                    <div key={chunk.id} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-deepBlue">
                          Chunk {index + 1}
                        </span>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          <span>{chunk.metadata.document_name}</span>
                          <span>Page {chunk.metadata.page_num}</span>
                          <span className="text-saffron font-medium">
                            Relevance: {(chunk.relevance_score * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700">{chunk.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="bg-gray-50 border border-lightGray rounded-lg p-4">
            <p className="text-sm text-gray-600">
              <strong>Disclaimer:</strong> This answer is generated by an AI system based on retrieved document chunks. 
              Always verify with original sources and consult qualified legal professionals for IP matters.
            </p>
            <div className="mt-3 pt-3 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                <strong>Jurisdiction Note:</strong> {jurisdiction === 'india' 
                  ? 'This answer covers Indian IP regimes (Patents Act, Biological Diversity Act, Drugs & Cosmetics Act, etc.)'
                  : 'This answer covers international IP regimes (TRIPS, CBD, Nagoya Protocol, WIPO treaties, etc.)'}
              </p>
            </div>
          </div>

          {/* Follow-up Questions */}
          {response && (
            <div className="bg-white border border-lightGray rounded-lg p-6">
              <h3 className="font-semibold text-deepBlue mb-4">Follow-up Questions</h3>
              <div className="space-y-2">
                {generateFollowUpQuestions(question, response.retrieved_chunks).map((followUp, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(followUp)}
                    className="w-full text-left p-3 bg-gray-50 border border-lightGray rounded-lg hover:border-deepBlue hover:bg-deepBlue/5 transition-colors text-sm flex items-center gap-2"
                  >
                    <span className="text-saffron">→</span>
                    <span>{followUp}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      </div>
      )}
    </div>
  )
}

export default AskIPSakti
