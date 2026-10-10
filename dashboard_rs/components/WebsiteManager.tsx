import { useState, useEffect } from 'react'
import { fetchApi } from '@/lib/api'
import { Loader2, Globe, ExternalLink, AlertCircle, RefreshCw, Store, X, Upload, Image as ImageIcon, Plus, Trash2, Check } from 'lucide-react'

export default function WebsiteManager() {
  const [websiteStatus, setWebsiteStatus] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showRequestForm, setShowRequestForm] = useState(false)
  const [websiteRequest, setWebsiteRequest] = useState<any>(null)
  const [loadingRequest, setLoadingRequest] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    websiteName: '',
    description: '',
    logo: null as File | null,
    logoPreview: null as string | null,
    colours: [] as string[],
    customColour: '#94D8AB',
    photos: [] as File[],
    photoPreviews: [] as string[]
  })

  // Validation errors
  const [formErrors, setFormErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)

  // Cleanup object URLs on unmount
  useEffect(() => {
    return () => {
      formData.photoPreviews.forEach(preview => {
        if (preview.startsWith('blob:')) {
          URL.revokeObjectURL(preview)
        }
      })
      if (formData.logoPreview && formData.logoPreview.startsWith('blob:')) {
        URL.revokeObjectURL(formData.logoPreview)
      }
    }
  }, [])

  const loadWebsiteStatus = async () => {
    try {
      setError(null)
      setLoading(true)
      const data = await fetchApi('/website/status/')
      setWebsiteStatus(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load website status')
    } finally {
      setLoading(false)
    }
  }

  const loadWebsiteRequest = async () => {
    try {
      setLoadingRequest(true)
      const data = await fetchApi('/website/request/')
      setWebsiteRequest(data)
    } catch (err: any) {
      // It's okay if there's no request yet
      setWebsiteRequest(null)
    } finally {
      setLoadingRequest(false)
    }
  }

  useEffect(() => {
    loadWebsiteStatus()
    loadWebsiteRequest()
  }, [])

  const handleRequestWebsite = () => {
    if (websiteRequest && websiteRequest.has_request) {
      // Already has an active request, show status
      return
    }
    setShowRequestForm(true)
  }

  const handleBackToStatus = () => {
    setShowRequestForm(false)
    // Reset form
    setFormData({
      websiteName: '',
      description: '',
      logo: null,
      logoPreview: null,
      colours: [],
      customColour: '#94D8AB',
      photos: [],
      photoPreviews: []
    })
    setFormErrors({})
  }

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate it's an image
      if (!file.type.startsWith('image/')) {
        setFormErrors({ ...formErrors, logo: 'Please select a valid image file' })
        return
      }
      
      // Create object URL for preview
      const previewUrl = URL.createObjectURL(file)
      
      setFormData({
        ...formData,
        logo: file,
        logoPreview: previewUrl
      })
      setFormErrors({ ...formErrors, logo: '' })
    }
  }

  const handleRemoveLogo = () => {
    // Clean up object URL if it exists
    if (formData.logoPreview && formData.logoPreview.startsWith('blob:')) {
      URL.revokeObjectURL(formData.logoPreview)
    }
    
    setFormData({
      ...formData,
      logo: null,
      logoPreview: null
    })
  }

  const handleAddColour = () => {
    if (!formData.colours.includes(formData.customColour)) {
      setFormData({
        ...formData,
        colours: [...formData.colours, formData.customColour]
      })
    }
  }

  const handleRemoveColour = (colour: string) => {
    setFormData({
      ...formData,
      colours: formData.colours.filter(c => c !== colour)
    })
  }

  const handlePhotosChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    const errors: Record<string, string> = { ...formErrors }

    // Reset the input value so the same files can be selected again if needed
    e.target.value = ''

    // Validate all files first
    const validFiles: File[] = []
    const invalidFileErrors: string[] = []
    
    files.forEach(file => {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        invalidFileErrors.push(`"${file.name}" is not a valid image file`)
        return
      }

      // Validate file size (2MB limit, files exactly 2MB are accepted)
      const maxSize = 2 * 1024 * 1024 // Exactly 2MB
      if (file.size > maxSize) {
        invalidFileErrors.push(`"${file.name}" exceeds 2MB limit (${(file.size / 1024 / 1024).toFixed(2)}MB)`)
        return
      }

      validFiles.push(file)
    })

    // Show errors for invalid files
    if (invalidFileErrors.length > 0) {
      errors.photos = invalidFileErrors.join('; ')
      setFormErrors(errors)
    } else {
      // Clear photo errors if all files in this batch are valid
      delete errors.photos
      setFormErrors(errors)
    }

    // If no valid files, do nothing
    if (validFiles.length === 0) {
      return
    }

    // Create object URLs for all valid files
    const newPreviews = validFiles.map(file => URL.createObjectURL(file))

    setFormData({
      ...formData,
      photos: [...formData.photos, ...validFiles],
      photoPreviews: [...formData.photoPreviews, ...newPreviews]
    })
  }

  const handleRemovePhoto = (index: number) => {
    // Clean up object URL if it exists
    const preview = formData.photoPreviews[index]
    if (preview && preview.startsWith('blob:')) {
      URL.revokeObjectURL(preview)
    }
    
    setFormData({
      ...formData,
      photos: formData.photos.filter((_, i) => i !== index),
      photoPreviews: formData.photoPreviews.filter((_, i) => i !== index)
    })
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}

    if (!formData.websiteName.trim()) {
      errors.websiteName = 'Website name is required'
    }

    if (formData.photos.length < 10) {
      errors.photos = `At least 10 photos are required. You have selected ${formData.photos.length} photo${formData.photos.length !== 1 ? 's' : ''}. Please add ${10 - formData.photos.length} more photo${10 - formData.photos.length !== 1 ? 's' : ''}.`
    }

    setFormErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async () => {
    // Always run validation to show clear messages
    if (!validateForm()) {
      return
    }

    setSubmitting(true)
    setFormErrors({})

    try {
      // Create FormData for multipart upload
      const formDataToSend = new FormData()
      formDataToSend.append('website_name', formData.websiteName)
      formDataToSend.append('description', formData.description)
      
      if (formData.logo) {
        formDataToSend.append('logo', formData.logo)
      }
      
      formDataToSend.append('colours', JSON.stringify(formData.colours))
      
      formData.photos.forEach((photo) => {
        formDataToSend.append('photos', photo)
      })

      const response = await fetchApi('/website/request/', {
        method: 'POST',
        body: formDataToSend,
        headers: {
          // Don't set Content-Type header for FormData, let browser set it with boundary
        }
      })

      // Success
      alert('Your website request has been submitted successfully! Our team will create your website in approximately one week. You will be notified when it is ready.')
      
      // Reset form and go back to status
      handleBackToStatus()
      
      // Reload website request status
      await loadWebsiteRequest()
      await loadWebsiteStatus()
    } catch (err: any) {
      // Handle backend validation errors
      console.error('Submission error:', err)
      
      const backendErrors = err.data || err.cause || (err.response && err.response.data) || {}
      const formattedErrors: Record<string, string> = {}
      
      if (backendErrors.website_name) {
        formattedErrors.websiteName = Array.isArray(backendErrors.website_name) 
          ? backendErrors.website_name[0] 
          : backendErrors.website_name
      }
      if (backendErrors.description) {
        formattedErrors.description = Array.isArray(backendErrors.description) 
          ? backendErrors.description[0] 
          : backendErrors.description
      }
      if (backendErrors.logo) {
        formattedErrors.logo = Array.isArray(backendErrors.logo) 
          ? backendErrors.logo[0] 
          : backendErrors.logo
      }
      if (backendErrors.colours) {
        formattedErrors.colours = Array.isArray(backendErrors.colours) 
          ? backendErrors.colours[0] 
          : backendErrors.colours
      }
      if (backendErrors.photos) {
        formattedErrors.photos = Array.isArray(backendErrors.photos) 
          ? backendErrors.photos[0] 
          : backendErrors.photos
      }
      if (backendErrors.detail) {
        formattedErrors.general = backendErrors.detail
      }
      
      if (Object.keys(formattedErrors).length === 0) {
        formattedErrors.general = err.message || 'Failed to submit request. Please try again.'
      }
      
      setFormErrors(formattedErrors)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col gap-6">
        <h1 className="text-2xl font-semibold">Website</h1>
        <div className="p-8 flex justify-center">
          <Loader2 className="animate-spin text-[#64748b]" />
        </div>
      </div>
    )
  }

  if (showRequestForm) {
    return (
      <div className="flex flex-col gap-6">
        <div className="flex items-center gap-4">
          <button
            onClick={handleBackToStatus}
            className="px-4 py-2 rounded-xl border border-[#D5E6DA] text-sm font-semibold text-[#64748b] hover:bg-[#F0FAF3] transition-colors"
          >
            ← Back
          </button>
          <div>
            <h1 className="text-2xl font-semibold">Website Request</h1>
            <p className="text-sm text-[#64748b]">Submit your website request with your branding materials.</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-[#D5E6DA]">
          {formErrors.general && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm mb-6">
              {formErrors.general}
            </div>
          )}

          <div className="space-y-8">
            {/* Website Name */}
            <div>
              <label className="block text-sm font-medium text-[#64748b] mb-2">
                Website Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.websiteName}
                onChange={(e) => {
                  setFormData({ ...formData, websiteName: e.target.value })
                  setFormErrors({ ...formErrors, websiteName: '' })
                }}
                placeholder="e.g., My Delicious Restaurant"
                className={`w-full rounded-xl border px-4 py-2.5 text-sm focus:border-[#94D8AB] focus:outline-none ${
                  formErrors.websiteName ? 'border-red-300 bg-red-50' : 'border-[#D5E6DA]'
                }`}
              />
              {formErrors.websiteName && (
                <p className="text-xs text-red-600 mt-1">{formErrors.websiteName}</p>
              )}
            </div>

            {/* Website Description */}
            <div>
              <label className="block text-sm font-medium text-[#64748b] mb-2">
                Website Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => {
                  setFormData({ ...formData, description: e.target.value })
                }}
                placeholder="Describe your restaurant website, preferred design, pages, features, or any special requirements..."
                rows={4}
                className="w-full rounded-xl border border-[#D5E6DA] px-4 py-2.5 text-sm focus:border-[#94D8AB] focus:outline-none resize-none"
              />
            </div>

            {/* Restaurant Logo */}
            <div>
              <label className="block text-sm font-medium text-[#64748b] mb-2">
                Restaurant Logo
              </label>
              {formData.logoPreview ? (
                <div className="relative inline-block">
                  <img
                    src={formData.logoPreview}
                    alt="Logo preview"
                    className="w-32 h-32 object-contain rounded-xl border border-[#D5E6DA]"
                  />
                  <button
                    onClick={handleRemoveLogo}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                    title="Remove logo"
                  >
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <div className="relative">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleLogoChange}
                    className="hidden"
                    id="logo-upload"
                  />
                  <label
                    htmlFor="logo-upload"
                    className="flex items-center justify-center gap-2 w-full rounded-xl border-2 border-dashed border-[#D5E6DA] py-8 cursor-pointer hover:border-[#94D8AB] hover:bg-[#F0FAF3] transition-colors"
                  >
                    <Upload size={24} className="text-[#64748b]" />
                    <span className="text-sm text-[#64748b]">Click to upload logo</span>
                  </label>
                </div>
              )}
              {formErrors.logo && (
                <p className="text-xs text-red-600 mt-1">{formErrors.logo}</p>
              )}
            </div>

            {/* Website Colours */}
            <div>
              <label className="block text-sm font-medium text-[#64748b] mb-2">
                Website Colours
              </label>
              <div className="flex gap-2 mb-3">
                <input
                  type="color"
                  value={formData.customColour}
                  onChange={(e) => setFormData({ ...formData, customColour: e.target.value })}
                  className="w-12 h-12 rounded-lg cursor-pointer border-0"
                />
                <button
                  onClick={handleAddColour}
                  className="px-4 py-2 rounded-xl border border-[#D5E6DA] text-sm font-semibold text-[#64748b] hover:bg-[#F0FAF3] transition-colors"
                >
                  Add Colour
                </button>
              </div>
              {formData.colours.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {formData.colours.map((colour, index) => (
                    <div
                      key={index}
                      className="relative group"
                    >
                      <div
                        className="w-10 h-10 rounded-lg border-2 border-gray-200"
                        style={{ backgroundColor: colour }}
                      />
                      <button
                        onClick={() => handleRemoveColour(colour)}
                        className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full p-0.5 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Restaurant Photos */}
            <div>
              <label className="block text-sm font-medium text-[#64748b] mb-2">
                Restaurant Photos <span className="text-red-500">*</span>
                <span className="text-xs text-[#94a3b8] ml-2">(Minimum 10 photos, max 2MB each)</span>
              </label>
              <div className="relative mb-4">
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handlePhotosChange}
                  className="hidden"
                  id="photos-upload"
                />
                <label
                  htmlFor="photos-upload"
                  className="flex items-center justify-center gap-2 w-full rounded-xl border-2 border-dashed border-[#D5E6DA] py-8 cursor-pointer hover:border-[#94D8AB] hover:bg-[#F0FAF3] transition-colors"
                >
                  <ImageIcon size={24} className="text-[#64748b]" />
                  <span className="text-sm text-[#64748b]">Click to upload photos</span>
                </label>
              </div>

              {/* Photo count indicator */}
              <div className={`text-sm mb-3 font-medium ${formData.photos.length >= 10 ? 'text-[#2F855A]' : 'text-[#64748b]'}`}>
                {formData.photos.length} / 10 minimum photos
                {formData.photos.length >= 10 && (
                  <span className="ml-2 flex items-center gap-1 inline-flex">
                    <Check size={14} />
                    Minimum met
                  </span>
                )}
              </div>

              {/* Persistent validation message for minimum photos */}
              {formData.photos.length < 10 && (
                <div className="bg-amber-50 border border-amber-200 text-amber-700 px-3 py-2 rounded-lg text-sm mb-3">
                  {formData.photos.length === 0 
                    ? 'At least 10 photos are required. Please upload photos to continue.'
                    : `You need ${10 - formData.photos.length} more photo${10 - formData.photos.length !== 1 ? 's' : ''} to meet the minimum requirement of 10 photos.`
                  }
                </div>
              )}

              {/* Photo previews */}
              {formData.photoPreviews.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {formData.photoPreviews.map((preview, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={preview}
                        alt={`Photo ${index + 1}`}
                        className="w-full h-32 object-cover rounded-lg border border-[#D5E6DA]"
                      />
                      <button
                        onClick={() => handleRemovePhoto(index)}
                        className="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                        title="Remove photo"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {formErrors.photos && (
                <div className="text-xs text-red-600 mt-2">
                  {formErrors.photos}
                </div>
              )}
            </div>

            {/* Submit Button */}
            <div className="flex gap-3 pt-4 border-t border-[#D5E6DA]">
              <button
                onClick={handleBackToStatus}
                className="flex-1 py-3 rounded-xl border border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="flex-1 py-3 rounded-xl bg-[#94D8AB] text-[#14532D] font-bold disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#7EC796] transition-colors"
              >
                {submitting ? 'Submitting...' : 'Submit Request'}
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold">Website</h1>
        <p className="text-sm text-[#64748b]">Manage your restaurant's online presence and website.</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
          <button
            onClick={loadWebsiteStatus}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 rounded-lg font-semibold text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {!error && websiteStatus && (
        <div className="bg-white p-6 rounded-2xl border border-[#D5E6DA]">
          {websiteStatus.has_website && websiteStatus.website_url ? (
            // Website exists
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="flex size-12 items-center justify-center rounded-xl bg-[#DCF3E3] text-[#2F855A]">
                  <Globe size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[#14532D]">Your Website is Live</h2>
                  <p className="text-sm text-[#64748b]">Your restaurant website is active and accessible.</p>
                </div>
              </div>

              <div className="border-t border-[#D5E6DA] pt-6">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-[#64748b] mb-2">Website URL</label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 rounded-xl border border-[#D5E6DA] bg-[#F0FAF3] px-4 py-2.5 text-sm text-[#14532D]">
                      {websiteStatus.website_url}
                    </div>
                    <a
                      href={websiteStatus.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 rounded-xl bg-[#94D8AB] px-4 py-2.5 text-sm font-bold text-[#14532D] hover:bg-[#7EC796] transition-colors"
                    >
                      <ExternalLink size={16} />
                      Open Website
                    </a>
                  </div>
                </div>
              </div>

              <div className="bg-[#DCF3E3] p-4 rounded-xl border border-[#94D8AB]">
                <div className="flex items-start gap-3">
                  <Store className="text-[#2F855A] mt-0.5" size={18} />
                  <div className="text-sm text-[#2f5d43]">
                    <p className="font-semibold mb-1">Website Status</p>
                    <p>Your website is currently published and accessible to customers. You can manage your website content and settings through the admin panel.</p>
                  </div>
                </div>
              </div>
            </div>
          ) : websiteRequest && websiteRequest.has_request ? (
            // Active request exists
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="flex size-12 items-center justify-center rounded-xl bg-[#DCF3E3] text-[#2F855A]">
                  <Globe size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[#14532D]">Website Request Submitted</h2>
                  <p className="text-sm text-[#64748b]">Your website request is being processed.</p>
                </div>
              </div>

              <div className="border-t border-[#D5E6DA] pt-6">
                <div className="bg-[#F0FAF3] p-6 rounded-xl border border-[#D5E6DA]">
                  <h3 className="font-semibold text-[#14532D] mb-4">Request Details</h3>
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Website Name:</span>
                      <span className="font-medium text-[#14532D]">{websiteRequest.request.website_name}</span>
                    </div>
                    {websiteRequest.request.description && (
                      <div>
                        <span className="text-[#64748b] block mb-1">Description:</span>
                        <span className="font-medium text-[#14532D] block">{websiteRequest.request.description}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Status:</span>
                      <span className={`font-medium px-2 py-0.5 rounded-full text-xs ${
                        websiteRequest.request.status === 'PENDING' ? 'bg-[#FBE3B5] text-[#92400E]' :
                        websiteRequest.request.status === 'IN_PROGRESS' ? 'bg-[#CFE0F7] text-[#1E40AF]' :
                        'bg-[#DCF3E3] text-[#2F855A]'
                      }`}>
                        {websiteRequest.request.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Submitted:</span>
                      <span className="font-medium text-[#14532D]">{new Date(websiteRequest.request.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#64748b]">Photos:</span>
                      <span className="font-medium text-[#14532D]">{websiteRequest.request.photos.length} photos</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-[#DCF3E3] p-4 rounded-xl border border-[#94D8AB]">
                <div className="flex items-start gap-3">
                  <Store className="text-[#2F855A] mt-0.5" size={18} />
                  <div className="text-sm text-[#2f5d43]">
                    <p className="font-semibold mb-1">What's Next?</p>
                    <p>Our team is working on creating your website. Website creation typically takes approximately one week. You will be notified when your website is ready to launch.</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // No website yet
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <div className="flex size-12 items-center justify-center rounded-xl bg-gray-100 text-gray-400">
                  <Globe size={24} />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[#14532D]">No Website Yet</h2>
                  <p className="text-sm text-[#64748b]">Your restaurant doesn't have a website yet.</p>
                </div>
              </div>

              <div className="border-t border-[#D5E6DA] pt-6">
                <div className="bg-[#F0FAF3] p-6 rounded-xl border border-[#D5E6DA]">
                  <h3 className="font-semibold text-[#14532D] mb-2">Get Your Restaurant Online</h3>
                  <p className="text-sm text-[#64748b] mb-4">
                    Request a professional website for your restaurant. Our team will create a custom website with your menu, photos, and branding.
                  </p>
                  <ul className="text-sm text-[#64748b] space-y-2 mb-6">
                    <li className="flex items-start gap-2">
                      <span className="text-[#2F855A] mt-1">•</span>
                      <span>Custom-designed restaurant website</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[#2F855A] mt-1">•</span>
                      <span>Online menu and ordering integration</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[#2F855A] mt-1">•</span>
                      <span>Mobile-responsive design</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-[#2F855A] mt-1">•</span>
                      <span>SEO optimization for local search</span>
                    </li>
                  </ul>
                  <button
                    onClick={handleRequestWebsite}
                    className="w-full rounded-xl bg-[#94D8AB] px-6 py-3 text-sm font-bold text-[#14532D] hover:bg-[#7EC796] transition-colors"
                  >
                    Make a Request
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
