import React, { useState, useEffect } from 'react'
import { Upload, FileText, CheckCircle, Clock, Tag, X } from 'lucide-react'

interface Document {
  name: string
  indexed_date: string
  page_count?: number
  chunk_count?: number
  status?: 'indexed' | 'processing' | 'pending'
  tags?: string[]
  jurisdiction?: 'india' | 'international'
  ip_regime?: string[]
}

const KnowledgeBase = () => {
  const [uploading, setUploading] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  
  const availableTags = ['Patents', 'GI', 'Trademarks', 'Copyright', 'ABS', 'TKDL', 'Biodiversity', 'Regulatory', 'Case Law']
  const jurisdictionOptions = ['india', 'international']
  const regimeOptions = ['patents', 'gi', 'trademarks', 'copyright', 'designs', 'trade_secrets', 'plant_variety', 'abs']

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return

    setUploading(true)
    
    for (const file of selectedFiles) {
      const formData = new FormData()
      formData.append('file', file)

      try {
        const res = await fetch('http://localhost:8000/upload', {
          method: 'POST',
          body: formData
        })
        const data = await res.json()
        
        // Add to documents list with default tags
        setDocuments(prev => [...prev, {
          name: data.document_name,
          indexed_date: new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }),
          page_count: data.page_count,
          chunk_count: data.chunk_count,
          status: 'indexed',
          tags: [],
          jurisdiction: 'india',
          ip_regime: []
        }])
      } catch (error) {
        console.error('Error uploading:', file.name, error)
      }
    }
    
    setSelectedFiles([])
    setUploading(false)
  }

  const addTag = (docName: string, tag: string) => {
    setDocuments(prev => prev.map(doc => 
      doc.name === docName 
        ? { ...doc, tags: [...(doc.tags || []), tag] }
        : doc
    ))
  }

  const removeTag = (docName: string, tagToRemove: string) => {
    setDocuments(prev => prev.map(doc => 
      doc.name === docName 
        ? { ...doc, tags: (doc.tags || []).filter(t => t !== tagToRemove) }
        : doc
    ))
  }

  const updateJurisdiction = (docName: string, jurisdiction: 'india' | 'international') => {
    setDocuments(prev => prev.map(doc => 
      doc.name === docName 
        ? { ...doc, jurisdiction }
        : doc
    ))
  }

  const toggleRegime = (docName: string, regime: string) => {
    setDocuments(prev => prev.map(doc => 
      doc.name === docName 
        ? { ...doc, ip_regime: (doc.ip_regime || []).includes(regime) 
            ? (doc.ip_regime || []).filter(r => r !== regime)
            : [...(doc.ip_regime || []), regime] }
        : doc
    ))
  }

  // Fetch documents on mount
  useEffect(() => {
    fetch('http://localhost:8000/documents')
      .then(res => res.json())
      .then(data => {
        setDocuments(data.documents.map((doc: any) => ({
          ...doc,
          status: 'indexed' as const,
          tags: [],
          jurisdiction: 'india',
          ip_regime: []
        })))
      })
      .catch(err => console.error('Error fetching documents:', err))
  }, [])

  return (
    <div className="max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-deepBlue mb-2">Knowledge Base</h1>
        <p className="text-gray-600">Upload and index IP documents for the RAG system.</p>
      </div>

      {/* Upload Section */}
      <div className="bg-white border border-lightGray rounded-lg p-6 mb-8">
        <h3 className="font-semibold text-deepBlue mb-4">Upload PDF Documents (Multiple)</h3>
        <div className="flex items-center gap-4">
          <label className="flex-1">
            <div className="border-2 border-dashed border-lightGray rounded-lg p-6 text-center cursor-pointer hover:border-deepBlue/50 transition-colors">
              <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">
                {selectedFiles.length > 0 
                  ? `${selectedFiles.length} file(s) selected` 
                  : 'Click to select PDF files (multiple allowed)'}
              </p>
            </div>
            <input
              type="file"
              accept=".pdf"
              multiple
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>
          <button
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || uploading}
            className="bg-deepBlue text-white px-6 py-3 rounded-lg hover:bg-blue-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? `Processing ${selectedFiles.length} file(s)...` : 'Upload & Index All'}
          </button>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white border border-lightGray rounded-lg">
        <div className="p-4 border-b border-lightGray">
          <h3 className="font-semibold text-deepBlue">Indexed Documents</h3>
        </div>
        {documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No documents indexed yet</p>
            <p className="text-sm">Upload a PDF to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-lightGray">
            {documents.map((doc, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-deepBlue/10 rounded-lg flex items-center justify-center">
                      <FileText className="w-5 h-5 text-deepBlue" />
                    </div>
                    <div>
                      <h4 className="font-medium text-deepBlue">{doc.name}</h4>
                      <div className="flex items-center gap-3 text-sm text-gray-500">
                        {doc.page_count && <span>{doc.page_count} pages</span>}
                        {doc.chunk_count && <span>{doc.chunk_count} chunks</span>}
                        <span>Indexed {doc.indexed_date}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.status === 'indexed' ? (
                      <span className="flex items-center gap-1 text-green-600 text-sm">
                        <CheckCircle className="w-4 h-4" />
                        Indexed
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-yellow-600 text-sm">
                        <Clock className="w-4 h-4" />
                        Processing
                      </span>
                    )}
                  </div>
                </div>
                
                {/* Tags */}
                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-2">
                    <Tag className="w-4 h-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Tags:</span>
                  </div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {(doc.tags || []).map((tag, tagIndex) => (
                      <span key={tagIndex} className="inline-flex items-center gap-1 px-2 py-1 bg-deepBlue/10 text-deepBlue rounded-full text-xs">
                        {tag}
                        <button
                          onClick={() => removeTag(doc.name, tag)}
                          className="hover:text-red-600"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {availableTags.filter(tag => !(doc.tags || []).includes(tag)).slice(0, 5).map((tag) => (
                      <button
                        key={tag}
                        onClick={() => addTag(doc.name, tag)}
                        className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs hover:bg-deepBlue/10 hover:text-deepBlue"
                      >
                        + {tag}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Jurisdiction & IP Regime */}
                <div className="flex gap-4">
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-700 mb-1 block">Jurisdiction:</span>
                    <div className="flex gap-2">
                      {jurisdictionOptions.map((jur) => (
                        <button
                          key={jur}
                          onClick={() => updateJurisdiction(doc.name, jur as 'india' | 'international')}
                          className={`px-3 py-1 text-xs rounded-full ${
                            doc.jurisdiction === jur
                              ? 'bg-deepBlue text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {jur === 'india' ? 'India' : 'International'}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex-1">
                    <span className="text-sm font-medium text-gray-700 mb-1 block">IP Regimes:</span>
                    <div className="flex flex-wrap gap-1">
                      {regimeOptions.map((regime) => (
                        <button
                          key={regime}
                          onClick={() => toggleRegime(doc.name, regime)}
                          className={`px-2 py-1 text-xs rounded-full ${
                            (doc.ip_regime || []).includes(regime)
                              ? 'bg-saffron text-white'
                              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                          }`}
                        >
                          {regime}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default KnowledgeBase
