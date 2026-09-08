import { useState } from 'react'
import { ChevronRight, AlertCircle } from 'lucide-react'

interface FormulationType {
  id: string
  name: string
  description: string
  ip_posture: string
  regulatory_requirements: string[]
  examples: string[]
  regulatory_checklist: {
    step: string
    description: string
    authority: string
    timeline: string
  }[]
}

const formulationTypes: FormulationType[] = [
  {
    id: 'classical',
    name: 'Classical Medicine',
    description: 'Formulation and method drawn from First-Schedule authoritative texts (Ayurvedic Pharmacopoeia, etc.)',
    ip_posture: 'Largely traditional knowledge; faces Section 3(p) patenting bar; defended through TKDL',
    regulatory_requirements: [
      'Must be listed in authoritative Ayurvedic texts',
      'No new clinical trials required',
      'Standard manufacturing under Drugs & Cosmetics Act',
      'Can be marketed as classical Ayurvedic medicine'
    ],
    examples: ['Chyawanprash', 'Triphala', 'Ashwagandha Churna'],
    regulatory_checklist: [
      { step: 'Verify classical status', description: 'Confirm formulation is listed in First Schedule texts', authority: 'Ayurvedic Pharmacopoeia Committee', timeline: '1-2 weeks' },
      { step: 'Obtain Ayush license', description: 'Apply for manufacturing license under Drugs & Cosmetics Act', authority: 'State Ayush Department', timeline: '8-12 weeks' },
      { step: 'TKDL verification', description: 'Check TKDL for prior art documentation', authority: 'CSIR-TKDL', timeline: '2-3 weeks' },
      { step: 'Quality standards', description: 'Ensure compliance with Ayurvedic Pharmacopoeia standards', authority: 'Pharmacopoeial Commission', timeline: 'Ongoing' }
    ]
  },
  {
    id: 'proprietary',
    name: 'Patent/Proprietary Medicine',
    description: 'Modified classical formulations or new combinations with documented traditional use',
    ip_posture: 'Limited patent potential; may qualify for trade secret protection; TKDL prior art check required',
    regulatory_requirements: [
      'Safety and efficacy documentation needed',
      'Standardization and quality control',
      'Manufacturing under GMP',
      'May require additional safety data'
    ],
    examples: ['Modified classical formulations', 'New combinations of known herbs'],
    regulatory_checklist: [
      { step: 'Formulation documentation', description: 'Document modifications and rationale', authority: 'Internal R&D', timeline: '2-4 weeks' },
      { step: 'Safety assessment', description: 'Conduct toxicology studies', authority: 'NABL accredited lab', timeline: '8-12 weeks' },
      { step: 'Efficacy validation', description: 'Generate clinical evidence', authority: 'Hospital/Clinical trial site', timeline: '12-24 weeks' },
      { step: 'ABS compliance', description: 'Check if biological resources require NBA approval', authority: 'NBA/SBB', timeline: '4-8 weeks' }
    ]
  },
  {
    id: 'new_drug',
    name: 'New Drug',
    description: 'Non-classical formulations requiring proof of safety and effectiveness',
    ip_posture: 'Genuine patent potential if novel and inventive; must pass Section 3(p) scrutiny',
    regulatory_requirements: [
      'Full pre-clinical and clinical trials',
      'Toxicity studies required',
      'CDSCO approval as new drug',
      'Extensive safety and efficacy documentation'
    ],
    examples: ['Novel single herb extracts', 'New molecular entities from plants'],
    regulatory_checklist: [
      { step: 'Pre-clinical studies', description: 'Conduct animal toxicity and pharmacokinetic studies', authority: 'GLP certified lab', timeline: '16-24 weeks' },
      { step: 'Phase I clinical trial', description: 'Safety study in healthy volunteers', authority: 'CDSCO approved site', timeline: '24-36 weeks' },
      { step: 'Phase II/III trials', description: 'Efficacy and safety in target population', authority: 'CDSCO approved site', timeline: '48-72 weeks' },
      { step: 'CDSCO approval', description: 'Submit NDA and obtain marketing authorization', authority: 'CDSCO', timeline: '24-52 weeks' }
    ]
  },
  {
    id: 'phytopharmaceutical',
    name: 'Phytopharmaceutical',
    description: 'Standardized plant-derived medicines with defined active constituents',
    ip_posture: 'Strong patent potential for extraction methods and formulations; process patents available',
    regulatory_requirements: [
      'Standardized to marker compounds',
      'Quality control specifications',
      'Clinical evidence for therapeutic claims',
      'Regulated under phytopharmaceutical guidelines'
    ],
    examples: ['Standardized curcumin formulations', 'Withanolide-based products'],
    regulatory_checklist: [
      { step: 'Standardization', description: 'Develop and validate analytical methods for marker compounds', authority: 'NABL accredited lab', timeline: '8-12 weeks' },
      { step: 'Quality specifications', description: 'Establish quality control parameters', authority: 'Internal QA', timeline: '4-6 weeks' },
      { step: 'Clinical validation', description: 'Generate clinical evidence for claims', authority: 'Clinical trial site', timeline: '24-48 weeks' },
      { step: 'Phytopharmaceutical approval', description: 'Submit under phytopharmaceutical guidelines', authority: 'CDSCO', timeline: '16-24 weeks' }
    ]
  },
  {
    id: 'nutraceutical',
    name: 'Ayurveda-Aahar / Nutraceutical',
    description: 'Food products with health benefits, regulated under FSSAI',
    ip_posture: 'Limited patent protection; trademark and trade secret protection more relevant',
    regulatory_requirements: [
      'FSSAI license and approval',
      'Food safety standards compliance',
      'Labeling as nutraceutical/functional food',
      'No therapeutic claims allowed'
    ],
    examples: ['Herbal health drinks', 'Fortified foods', 'Dietary supplements'],
    regulatory_checklist: [
      { step: 'FSSAI license', description: 'Obtain food license and registration', authority: 'FSSAI', timeline: '2-4 weeks' },
      { step: 'Product approval', description: 'Submit for nutraceutical approval', authority: 'FSSAI', timeline: '8-12 weeks' },
      { step: 'Labeling compliance', description: 'Ensure labeling meets FSSAI standards', authority: 'FSSAI', timeline: '2-3 weeks' },
      { step: 'Safety testing', description: 'Conduct food safety testing', authority: 'NABL accredited lab', timeline: '4-6 weeks' }
    ]
  },
  {
    id: 'cosmetic',
    name: 'Cosmetic',
    description: 'Products for external use with cosmetic benefits',
    ip_posture: 'Formula patents possible; trademark and design protection common',
    regulatory_requirements: [
      'Drugs & Cosmetics Act compliance',
      'No therapeutic claims permitted',
      'Safety assessment required',
      'Labeling as cosmetic product'
    ],
    examples: ['Herbal creams', 'Ayurvedic hair oils', 'Natural skincare products'],
    regulatory_checklist: [
      { step: 'Cosmetic license', description: 'Obtain cosmetic manufacturing license', authority: 'State FDA', timeline: '4-6 weeks' },
      { step: 'Safety assessment', description: 'Conduct cosmetic safety testing', authority: 'NABL accredited lab', timeline: '6-8 weeks' },
      { step: 'Labeling approval', description: 'Ensure labeling complies with cosmetic regulations', authority: 'State FDA', timeline: '2-3 weeks' },
      { step: 'Product registration', description: 'Register cosmetic product', authority: 'CDSCO', timeline: '4-6 weeks' }
    ]
  }
]

const FormulationClassifier = () => {
  const [answers, setAnswers] = useState<Record<string, string>>({})

  const classificationQuestions = [
    {
      id: 'source',
      question: 'Is your formulation documented in authoritative Ayurvedic texts (First Schedule)?',
      options: ['Yes, exactly as described', 'Yes, but modified', 'No, completely new']
    },
    {
      id: 'intended_use',
      question: 'What is the primary intended use of your product?',
      options: ['Therapeutic treatment', 'Health supplement', 'Cosmetic enhancement', 'Food product']
    },
    {
      id: 'biological_source',
      question: 'What is the source of biological resources in your formulation?',
      options: ['Wild-harvested from India', 'Cultivated in India', 'Imported from abroad', 'Synthetic/semi-synthetic']
    },
    {
      id: 'abs_compliance',
      question: 'Have you obtained necessary ABS approvals for biological resource access?',
      options: ['Yes, NBA/SBB approval obtained', 'Applied and pending', 'Not required (synthetic)', 'Not yet applied']
    },
    {
      id: 'novelty',
      question: 'Does your formulation involve novel extraction methods or new combinations?',
      options: ['Yes, novel extraction', 'Yes, new combination', 'No, traditional method']
    },
    {
      id: 'clinical_evidence',
      question: 'Do you have clinical evidence supporting safety and efficacy?',
      options: ['Full clinical trials', 'Pre-clinical studies only', 'Traditional use documentation', 'No evidence yet']
    }
  ]

  const handleAnswer = (questionId: string, answer: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const classifyFormulation = () => {
    // Enhanced classification logic based on answers
    const { source, intended_use, novelty, clinical_evidence } = answers

    if (source === 'Yes, exactly as described' && intended_use === 'Therapeutic treatment') {
      return 'classical'
    }
    if (source === 'Yes, but modified' && intended_use === 'Therapeutic treatment') {
      return 'proprietary'
    }
    if (source === 'No, completely new' && clinical_evidence === 'Full clinical trials') {
      return 'new_drug'
    }
    if (novelty === 'Yes, novel extraction' && intended_use === 'Therapeutic treatment') {
      return 'phytopharmaceutical'
    }
    if (intended_use === 'Food product' || intended_use === 'Health supplement') {
      return 'nutraceutical'
    }
    if (intended_use === 'Cosmetic enhancement') {
      return 'cosmetic'
    }
    return 'proprietary' // default
  }

  const recommendedType = formulationTypes.find(t => t.id === classifyFormulation())
  
  // Check ABS compliance warning
  const needsABS = answers.biological_source === 'Wild-harvested from India' || answers.biological_source === 'Cultivated in India'
  const absWarning = needsABS && answers.abs_compliance !== 'Yes, NBA/SBB approval obtained'

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deepBlue mb-2">Formulation Classifier</h1>
        <p className="text-gray-600">
          Determine your Ayurvedic product's regulatory category and understand its IP implications.
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
          <div>
            <p className="text-sm text-yellow-800 font-medium">Important Note</p>
            <p className="text-sm text-yellow-700 mt-1">
              This classifier provides initial guidance based on your responses. For definitive classification,
              consult with regulatory experts and IP professionals. The IP posture varies significantly between categories.
            </p>
          </div>
        </div>
      </div>

      {/* Classification Questions */}
      <div className="space-y-6 mb-8">
        {classificationQuestions.map((q, index) => (
          <div key={q.id} className="bg-white border border-lightGray rounded-lg p-6">
            <div className="flex items-start gap-3 mb-4">
              <span className="flex items-center justify-center w-8 h-8 bg-deepBlue text-white rounded-full text-sm font-medium">
                {index + 1}
              </span>
              <h3 className="font-semibold text-deepBlue">{q.question}</h3>
            </div>
            <div className="space-y-2 ml-11">
              {q.options.map((option) => (
                <button
                  key={option}
                  onClick={() => handleAnswer(q.id, option)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    answers[q.id] === option
                      ? 'border-deepBlue bg-deepBlue/5 text-deepBlue'
                      : 'border-lightGray hover:border-deepBlue/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      answers[q.id] === option ? 'border-deepBlue bg-deepBlue' : 'border-gray-300'
                    }`} />
                    <span className="text-sm">{option}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Classification Result */}
      {recommendedType && (
        <div className="bg-white border border-lightGray rounded-lg p-6">
          <div className="flex items-center gap-3 mb-4">
            <ChevronRight className="w-5 h-5 text-saffron" />
            <h3 className="font-semibold text-deepBlue text-lg">Recommended Classification</h3>
          </div>
          
          <div className="mb-6">
            <h4 className="text-xl font-bold text-deepBlue mb-2">{recommendedType.name}</h4>
            <p className="text-gray-600">{recommendedType.description}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h5 className="font-semibold text-deepBlue mb-2">IP Posture</h5>
              <p className="text-sm text-gray-700">{recommendedType.ip_posture}</p>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h5 className="font-semibold text-green-800 mb-2">Regulatory Requirements</h5>
              <ul className="text-sm text-gray-700 space-y-1">
                {recommendedType.regulatory_requirements.map((req, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-green-600">•</span>
                    <span>{req}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-6 bg-gray-50 border border-lightGray rounded-lg p-4">
            <h5 className="font-semibold text-gray-700 mb-2">Examples</h5>
            <div className="flex flex-wrap gap-2">
              {recommendedType.examples.map((example, i) => (
                <span key={i} className="px-3 py-1 bg-white border border-lightGray rounded-full text-sm text-gray-600">
                  {example}
                </span>
              ))}
            </div>
          </div>

          {/* Regulatory Pathway Checklist */}
          <div className="mt-6 bg-white border border-lightGray rounded-lg p-6">
            <h5 className="font-semibold text-deepBlue mb-4">Regulatory Pathway Checklist</h5>
            <div className="space-y-4">
              {recommendedType.regulatory_checklist.map((item, index) => (
                <div key={index} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg border border-lightGray">
                  <div className="flex items-center justify-center w-8 h-8 bg-deepBlue text-white rounded-full text-sm font-medium flex-shrink-0">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-start justify-between mb-2">
                      <h6 className="font-semibold text-deepBlue">{item.step}</h6>
                      <span className="text-xs px-2 py-1 bg-saffron/10 text-saffron rounded-full">
                        {item.timeline}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{item.description}</p>
                    <p className="text-xs text-gray-500">
                      <strong>Authority:</strong> {item.authority}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 p-4 bg-saffron/10 border border-saffron/30 rounded-lg">
            <p className="text-sm text-gray-700">
              <strong>Next Steps:</strong> Based on this classification, you should:
              <ul className="mt-2 space-y-1 ml-4">
                <li>• Review the specific regulatory requirements for this category</li>
                <li>• Assess IP protection options based on the posture described</li>
                <li>• Consult with regulatory experts for compliance guidance</li>
                <li>• Consider ABS compliance if using biological resources</li>
              </ul>
            </p>
          </div>

          {/* ABS Compliance Warning */}
          {absWarning && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-red-800">ABS Compliance Required</p>
                  <p className="text-sm text-red-700 mt-1">
                    Your formulation uses biological resources from India. Under the Biological Diversity Act, 2002 (amended 2023), 
                    you must obtain prior approval from the National Biodiversity Authority (NBA) or State Biodiversity Board (SBB) 
                    before accessing these resources. Non-compliance can result in penalties and legal action.
                  </p>
                  <p className="text-sm text-red-700 mt-2">
                    <strong>Action Required:</strong> Apply for ABS approval through Form I to the NBA/SBB before proceeding with commercialization.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default FormulationClassifier
