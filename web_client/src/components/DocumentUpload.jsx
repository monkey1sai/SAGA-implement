import React, { useState, useRef, useCallback } from "react";

/**
 * 文件上傳元件
 * 
 * 支援：
 * - 拖放上傳
 * - 點擊選擇
 * - 上傳進度
 * - 多種格式（PDF、DOCX、TXT、MD）
 */

export default function DocumentUpload({ ragUrl, onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  
  const fileInputRef = useRef(null);
  
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);
  
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  }, []);
  
  const handleFileSelect = useCallback((e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  }, []);
  
  const uploadFile = useCallback(async (file) => {
    // 檢查檔案類型
    const allowedTypes = [".pdf", ".docx", ".txt", ".md", ".markdown"];
    const ext = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];
    
    if (!allowedTypes.includes(ext)) {
      setError(`不支援的檔案格式: ${ext}。支援: ${allowedTypes.join(", ")}`);
      return;
    }
    
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append("file", file);
      
      const response = await fetch(`${ragUrl}/ingest/file`, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `上傳失敗: ${response.status}`);
      }
      
      const result = await response.json();
      setUploadProgress(100);
      
      // 通知父元件
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (err) {
      console.error("上傳錯誤:", err);
      setError(err.message);
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      
      // 清除 input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [ragUrl, onUploadSuccess]);
  
  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);
  
  return (
    <div className="document-upload">
      <div
        className={`upload-zone ${isDragging ? "dragging" : ""} ${isUploading ? "uploading" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md,.markdown"
          onChange={handleFileSelect}
          style={{ display: "none" }}
        />
        
        {isUploading ? (
          <div className="upload-progress">
            <span className="upload-icon">📄</span>
            <span>上傳中... {uploadProgress}%</span>
          </div>
        ) : (
          <div className="upload-hint">
            <span className="upload-icon">📁</span>
            <span>拖放或點擊上傳文件</span>
          </div>
        )}
      </div>
      
      {error && (
        <div className="upload-error">
          ❌ {error}
        </div>
      )}
    </div>
  );
}
