import { ArrowRight, Database, FileText, Brain, MessageSquare } from 'lucide-react'

const About = () => {
  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deepBlue mb-2">About IP-SAKTI Sahayak</h1>
        <p className="text-gray-600">Understanding the RAG system behind the assistant.</p>
      </div>

      {/* How RAG Works */}
      <div className="bg-white border border-lightGray rounded-lg p-8 mb-8">
        <h2 className="text-2xl font-bold text-deepBlue mb-6">HOW RAG WORKS</h2>
        
        <div className="space-y-6">
          {/* Step 1 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              1
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Document Ingestion</h3>
              <p className="text-gray-600 text-sm">
                PDF documents are processed using PyMuPDF to extract text. Each page is tracked separately 
                to ensure accurate citation.
              </p>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              2
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Chunking</h3>
              <p className="text-gray-600 text-sm">
                Text is divided into page-aware chunks of ~500 characters with 50-character overlap. 
                Each chunk retains its document name and page number.
              </p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              3
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Embedding Generation</h3>
              <p className="text-gray-600 text-sm">
                Sentence Transformers (all-MiniLM-L6-v2) converts each chunk into a 384-dimensional vector 
                representation for semantic search.
              </p>
            </div>
          </div>

          {/* Step 4 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              4
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Vector Storage</h3>
              <p className="text-gray-600 text-sm">
                ChromaDB stores chunks and embeddings using cosine similarity for fast retrieval. 
                The vector index persists across sessions.
              </p>
            </div>
          </div>

          {/* Step 5 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              5
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Query Processing</h3>
              <p className="text-gray-600 text-sm">
                User questions are embedded and the top 5 most similar chunks are retrieved based on 
                semantic similarity scores.
              </p>
            </div>
          </div>

          {/* Step 6 */}
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-deepBlue rounded-full flex items-center justify-center text-white font-bold flex-shrink-0">
              6
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-deepBlue mb-2">Answer Generation</h3>
              <p className="text-gray-600 text-sm">
                Retrieved chunks are added as context to a Groq API prompt (Llama 3). The LLM is instructed 
                to answer using ONLY the provided context and cite sources.
              </p>
            </div>
          </div>
        </div>

        {/* Flow Diagram */}
        <div className="mt-8 p-6 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-lightGray">
              <MessageSquare className="w-5 h-5 text-deepBlue" />
              <span className="text-sm font-medium">User Query</span>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-lightGray">
              <Database className="w-5 h-5 text-deepBlue" />
              <span className="text-sm font-medium">Vector Search</span>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-lightGray">
              <FileText className="w-5 h-5 text-deepBlue" />
              <span className="text-sm font-medium">Top 5 Chunks</span>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-lightGray">
              <Brain className="w-5 h-5 text-deepBlue" />
              <span className="text-sm font-medium">LLM + Context</span>
            </div>
            <ArrowRight className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2 bg-saffron/10 px-4 py-2 rounded-lg border border-saffron/30">
              <MessageSquare className="w-5 h-5 text-saffron" />
              <span className="text-sm font-medium text-saffron">Cited Answer</span>
            </div>
          </div>
        </div>
      </div>

      {/* Technology Stack */}
      <div className="bg-white border border-lightGray rounded-lg p-6 mb-8">
        <h2 className="text-xl font-bold text-deepBlue mb-4">Technology Stack</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold text-deepBlue mb-2">Backend</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• Python + FastAPI</li>
              <li>• ChromaDB (Vector Database)</li>
              <li>• Sentence Transformers (Embeddings)</li>
              <li>• PyMuPDF (PDF Processing)</li>
              <li>• Groq API (LLM)</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-deepBlue mb-2">Frontend</h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>• React + TypeScript</li>
              <li>• Tailwind CSS</li>
              <li>• React Router</li>
              <li>• Lucide Icons</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-gray-50 border border-lightGray rounded-lg p-6">
        <h3 className="font-semibold text-deepBlue mb-2">Disclaimer</h3>
        <p className="text-sm text-gray-600">
          IP-SAKTI Sahayak is an academic prototype developed for Smart India Hackathon 2024. 
          The system provides AI-assisted informational guidance based on retrieved documents. 
          Content is for informational purposes only and does not constitute legal advice. 
          Always consult qualified legal professionals for IP matters.
        </p>
      </div>
    </div>
  )
}

export default About
