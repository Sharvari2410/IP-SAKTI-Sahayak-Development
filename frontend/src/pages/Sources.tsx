import { useState, useEffect } from 'react'
import { FileText, ExternalLink, CheckCircle } from 'lucide-react'

interface SourceDocument {
  name: string
  author?: string
  type?: string
  page_count?: number
  indexed_date: string
}

const Sources = () => {
  const [documents, setDocuments] = useState<SourceDocument[]>([])

  useEffect(() => {
    fetch('http://localhost:8000/documents')
      .then(res => res.json())
      .then(data => {
        setDocuments(data.documents.map((doc: any) => ({
          ...doc,
          author: 'Unknown',
          type: 'Document',
          page_count: 0
        })))
      })
      .catch(err => console.error('Error fetching documents:', err))
  }, [])

  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'Government Report': 'bg-blue-100 text-blue-700',
      'Regulatory Manual': 'bg-purple-100 text-purple-700',
      'Legislation': 'bg-green-100 text-green-700',
      'Policy Paper': 'bg-orange-100 text-orange-700',
      'Regulatory Guide': 'bg-teal-100 text-teal-700',
    }
    return colors[type] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deepBlue mb-2">Source Library</h1>
        <p className="text-gray-600">Documents currently indexed in the knowledge base.</p>
      </div>

      <div className="space-y-4">
        {documents.length === 0 ? (
          <div className="bg-white border border-lightGray rounded-lg p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No sources indexed yet</p>
            <p className="text-sm">Upload documents in the Knowledge Base to add sources</p>
          </div>
        ) : (
          documents.map((doc, index) => (
            <div key={index} className="bg-white border border-lightGray rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-semibold text-deepBlue text-lg">{doc.name}</h3>
                    <span className="px-2 py-1 bg-saffron/10 text-saffron text-xs rounded-full">
                      Demo Knowledge Source
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{doc.author}</p>
                  <div className="flex items-center gap-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${getDocumentTypeColor(doc.type || 'Document')}`}>
                      {doc.type || 'Document'}
                    </span>
                    {doc.page_count && <span className="text-gray-500">{doc.page_count} pages</span>}
                    <span className="text-gray-500">Indexed {doc.indexed_date}</span>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Indexed
                  </span>
                  <button className="flex items-center gap-2 text-deepBlue hover:text-blue-700 text-sm font-medium">
                    View document
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default Sources
