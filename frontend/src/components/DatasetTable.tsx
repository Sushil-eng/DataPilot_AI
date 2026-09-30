import React, { useState, useMemo } from 'react';
import { 
  Search, 
  ArrowDownUp, 
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Check,
  Plus,
  Trash2,
  AlertCircle,
  Eye,
  FileJson,
  FileSpreadsheet,
  X
} from 'lucide-react';
import { Card, Button, Input, Select, Checkbox } from '@/components';
import { downloadDatasetExport } from '@/services/api';
import type { DatasetRecord, DatasetSchemaField } from '@/services/api';
import { cn } from '@/utils/cn';


interface DatasetTableProps {
  datasetId?: string;
  datasetName?: string;
  schema?: DatasetSchemaField[];
  records: DatasetRecord[];
  isLoading?: boolean;
  onDeleteRecord?: (recordId: string) => Promise<void>;
  onAddRecord?: (recordData: Record<string, any>) => Promise<void>;
}

// Helper to format field key to human-readable header label
const formatHeaderLabel = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/\b\w/g, char => char.toUpperCase());
};

// ── Currency symbol lookup ──
const CURRENCY_SYMBOLS: Record<string, string> = {
  INR: '₹', USD: '$', EUR: '€', GBP: '£', JPY: '¥', CNY: '¥',
  KRW: '₩', BRL: 'R$', RUB: '₽', AUD: 'A$', CAD: 'C$', CHF: 'CHF',
  SGD: 'S$', HKD: 'HK$', MXN: 'MX$', ZAR: 'R', SEK: 'kr', NOK: 'kr',
  DKK: 'kr', PLN: 'zł', THB: '฿', IDR: 'Rp', TRY: '₺', AED: 'د.إ',
  SAR: '﷼', PHP: '₱', MYR: 'RM', NZD: 'NZ$', TWD: 'NT$', ARS: 'AR$',
};

// ── Smart formatting helpers ──

/**
 * Format a currency object like { amount: 25000, currency: "INR" }
 * into a readable string like "₹25,000 INR"
 */
const formatCurrencyObject = (obj: any): string | null => {
  if (!obj || typeof obj !== 'object') return null;

  // Handle { amount, currency } pattern
  const amount = obj.amount ?? obj.value ?? obj.price ?? obj.total;
  const currency = obj.currency ?? obj.unit ?? obj.code;

  if (amount !== undefined && amount !== null && !isNaN(Number(amount))) {
    const num = Number(amount);
    const sym = currency ? (CURRENCY_SYMBOLS[String(currency).toUpperCase()] || '') : '';
    const formatted = num.toLocaleString('en-IN', { 
      maximumFractionDigits: 2,
      minimumFractionDigits: 0,
    });
    if (sym && currency) {
      return `${sym}${formatted} ${String(currency).toUpperCase()}`;
    }
    if (sym) return `${sym}${formatted}`;
    return formatted;
  }

  return null;
};

/**
 * Format a plain number based on magnitude
 */
const formatNumber = (val: number): string => {
  if (Math.abs(val) >= 1_000_000_000) {
    return `${(val / 1_000_000_000).toFixed(1)}B`;
  }
  if (Math.abs(val) >= 1_000_000) {
    return `${(val / 1_000_000).toFixed(1)}M`;
  }
  return val.toLocaleString('en-IN');
};

/**
 * Extract domain from a URL for display
 */
const shortenUrl = (url: string): string => {
  try {
    const parsed = new URL(url);
    return parsed.hostname.replace(/^www\./, '');
  } catch {
    // fallback – strip protocol
    return url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0];
  }
};

/**
 * Format a date value to a readable string
 */
const formatDate = (val: any): string | null => {
  if (!val) return null;
  const d = new Date(val);
  if (isNaN(d.getTime())) return null;
  return d.toLocaleDateString('en-IN', { 
    year: 'numeric', month: 'short', day: 'numeric' 
  });
};

/**
 * Format an array into a readable comma-separated string
 */
const formatArray = (arr: any[]): string => {
  return arr
    .map(item => {
      if (item === null || item === undefined) return '';
      if (typeof item === 'object') return JSON.stringify(item);
      return String(item);
    })
    .filter(Boolean)
    .join(', ');
};

/**
 * Detect if a string looks like a URL
 */
const isUrlString = (val: string): boolean => {
  return /^https?:\/\//i.test(val);
};

/**
 * Detect if a string looks like an ISO date
 */
const isIsoDate = (val: string): boolean => {
  return /^\d{4}-\d{2}-\d{2}(T|\s)/.test(val);
};

/**
 * Get the minimum width CSS class for a column based on field type / name heuristics
 */
const getColumnMinWidth = (colName: string, fieldType?: string): string => {
  const lc = colName.toLowerCase();
  const type = (fieldType || '').toLowerCase();

  // URL columns
  if (type === 'url' || lc.includes('url') || lc.includes('website') || lc.includes('link')) {
    return 'min-w-[160px]';
  }
  // Currency / money
  if (type === 'currency' || lc.includes('revenue') || lc.includes('market_cap') || 
      lc.includes('salary') || lc.includes('price') || lc.includes('amount')) {
    return 'min-w-[140px]';
  }
  // Numbers
  if (type === 'number' || type === 'integer' || lc.includes('count') || lc.includes('rank')) {
    return 'min-w-[100px]';
  }
  // Date
  if (type === 'date' || type === 'datetime' || lc.includes('date') || lc.includes('year') || lc.includes('founded')) {
    return 'min-w-[110px]';
  }
  // Name-like
  if (lc.includes('name') || lc.includes('title') || lc.includes('company') || lc.includes('headquarters')) {
    return 'min-w-[180px]';
  }
  // Array
  if (type === 'array' || type === 'list') {
    return 'min-w-[180px]';
  }
  // Boolean
  if (type === 'boolean' || type === 'bool') {
    return 'min-w-[80px]';
  }
  // Default
  return 'min-w-[120px]';
};


export const DatasetTable: React.FC<DatasetTableProps> = ({
  datasetId,
  datasetName = 'Dataset',
  schema = [],
  records = [],
  isLoading = false,
  onDeleteRecord,
  onAddRecord,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilterField, setSelectedFilterField] = useState<string>('All');
  const [selectedFilterValue, setSelectedFilterValue] = useState<string>('All');
  
  const [sortConfig, setSortConfig] = useState<{ key: string | null; direction: 'asc' | 'desc' }>({
    key: null,
    direction: 'asc',
  });
  
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  
  const [exportingFormat, setExportingFormat] = useState<'csv' | 'json' | null>(null);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // New Record Form State
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRecordData, setNewRecordData] = useState<Record<string, string>>({});
  const [isSubmittingRecord, setIsSubmittingRecord] = useState(false);

  // Detail Modal State
  const [viewingRecord, setViewingRecord] = useState<DatasetRecord | null>(null);

  // Build a lookup map from schema field name → type
  const schemaTypeMap = useMemo(() => {
    const map: Record<string, string> = {};
    schema.forEach(field => {
      map[field.name] = field.type;
    });
    return map;
  }, [schema]);

  // DYNAMICALLY GENERATE COLUMNS
  const columns = useMemo(() => {
    const colSet = new Set<string>();

    // 1. Add fields defined in schema
    if (schema && schema.length > 0) {
      schema.forEach(field => colSet.add(field.name));
    }

    // 2. Extract keys present in record data objects
    records.forEach(rec => {
      const dataObj = rec.data || rec;
      if (typeof dataObj === 'object' && dataObj !== null) {
        Object.keys(dataObj).forEach(key => {
          if (!['_id', 'id', 'dataset_id', 'created_at', 'updated_at'].includes(key)) {
            colSet.add(key);
          }
        });
      }
    });

    return Array.from(colSet);
  }, [schema, records]);

  // Extract categorical field filters dynamically (fields with limited distinct string values)
  const filterableFields = useMemo(() => {
    return columns.filter(col => {
      const values = new Set<string>();
      records.forEach(rec => {
        const val = rec.data?.[col];
        if (val !== undefined && val !== null) values.add(String(val));
      });
      return values.size > 1 && values.size <= 15;
    });
  }, [columns, records]);

  // Unique values for the selected filter field
  const filterOptions = useMemo(() => {
    if (selectedFilterField === 'All') return [];
    const values = new Set<string>();
    records.forEach(rec => {
      const val = rec.data?.[selectedFilterField];
      if (val !== undefined && val !== null) values.add(String(val));
    });
    return Array.from(values).sort();
  }, [selectedFilterField, records]);

  // FILTERING & SORTING
  const filteredData = useMemo(() => {
    let result = records;

    // Global Search across all fields
    if (searchQuery.trim()) {
      const lowerQuery = searchQuery.toLowerCase();
      result = result.filter(rec => {
        const dataObj = rec.data || rec;
        return Object.values(dataObj).some(val => 
          val !== null && val !== undefined && String(val).toLowerCase().includes(lowerQuery)
        );
      });
    }

    // Categorical Filter
    if (selectedFilterField !== 'All' && selectedFilterValue !== 'All') {
      result = result.filter(rec => String(rec.data?.[selectedFilterField]) === selectedFilterValue);
    }

    // Sorting
    if (sortConfig.key) {
      const k = sortConfig.key;
      result = [...result].sort((a, b) => {
        const valA = a.data?.[k] ?? '';
        const valB = b.data?.[k] ?? '';

        if (typeof valA === 'number' && typeof valB === 'number') {
          return sortConfig.direction === 'asc' ? valA - valB : valB - valA;
        }

        const strA = String(valA).toLowerCase();
        const strB = String(valB).toLowerCase();
        if (strA < strB) return sortConfig.direction === 'asc' ? -1 : 1;
        if (strA > strB) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [records, searchQuery, selectedFilterField, selectedFilterValue, sortConfig]);

  // Pagination
  const totalPages = Math.ceil(filteredData.length / rowsPerPage);
  const paginatedData = filteredData.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  // Sorting Handler
  const handleSort = (key: string) => {
    let direction: 'asc' | 'desc' = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Selection Handlers
  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
      setSelectedRows(new Set(paginatedData.map(row => row.id)));
    } else {
      setSelectedRows(new Set());
    }
  };

  const handleSelectRow = (id: string) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  // Export Handler (Supports Backend Export Endpoint & Fallback)
  const handleExport = async (format: 'csv' | 'json') => {
    setExportingFormat(format);
    setExportError(null);
    setExportSuccess(null);

    const safeName = (datasetName || 'dataset').toLowerCase().replace(/\s+/g, '_');

    try {
      if (datasetId) {
        // Backend API Download
        const filename = `${safeName}_export.${format}`;
        await downloadDatasetExport(datasetId, format, filename);
      } else {
        // Client-side fallback
        if (filteredData.length === 0) return;

        if (format === 'json') {
          const exportData = filteredData.map(r => r.data || r);
          const jsonString = JSON.stringify(exportData, null, 2);
          const blob = new Blob([jsonString], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.setAttribute('download', `${safeName}_export.json`);
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        } else {
          const headers = columns.join(',');
          const csvRows = filteredData.map(rec => {
            return columns.map(col => {
              const val = rec.data?.[col] ?? '';
              const cleanVal = String(val).replace(/\r\n/g, ' ').replace(/\n/g, ' ').replace(/\r/g, ' ').replace(/"/g, '""');
              return `"${cleanVal}"`;
            }).join(',');
          });
          const csvContent = "\uFEFF" + [headers, ...csvRows].join("\r\n");
          const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.setAttribute("download", `${safeName}_export.csv`);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
        }
      }

      setExportSuccess(`Exported as ${format.toUpperCase()}`);
      setTimeout(() => setExportSuccess(null), 3000);
    } catch (err: any) {
      console.error("Export error", err);
      setExportError(err.message || `Failed to export as ${format.toUpperCase()}`);
    } finally {
      setExportingFormat(null);
    }
  };

  // Submit New Record
  const handleCreateRecordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onAddRecord) return;
    setIsSubmittingRecord(true);
    try {
      await onAddRecord(newRecordData);
      setNewRecordData({});
      setShowAddModal(false);
    } catch (err) {
      console.error("Add record error", err);
    } finally {
      setIsSubmittingRecord(false);
    }
  };

  // ── Smart cell renderer based on schema type + value introspection ──
  const renderCellContent = (value: any, colName: string) => {
    // Null / empty / undefined
    if (value === undefined || value === null || value === '') {
      return <span className="text-dp-text-muted select-none">—</span>;
    }

    const fieldType = (schemaTypeMap[colName] || '').toLowerCase();
    const colLower = colName.toLowerCase();

    // ── Boolean ──
    if (typeof value === 'boolean' || fieldType === 'boolean' || fieldType === 'bool') {
      const boolVal = typeof value === 'boolean' ? value : (String(value).toLowerCase() === 'true');
      return (
        <span className={cn(
          "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
          boolVal 
            ? "bg-dp-success/15 text-dp-success border border-dp-success/30" 
            : "bg-dp-bg-surface text-dp-text-muted border border-dp-border"
        )}>
          {boolVal ? 'Yes' : 'No'}
        </span>
      );
    }

    // ── Object (currency / nested) ──
    if (typeof value === 'object' && !Array.isArray(value)) {
      // Try currency formatting first
      const currencyFormatted = formatCurrencyObject(value);
      if (currencyFormatted) {
        return <span className="font-medium text-dp-text tabular-nums">{currencyFormatted}</span>;
      }

      // Fallback: render key-value pairs in a compact readable way
      const entries = Object.entries(value).filter(([, v]) => v !== null && v !== undefined);
      if (entries.length === 0) return <span className="text-dp-text-muted select-none">—</span>;
      
      return (
        <span className="text-xs text-dp-text-secondary leading-relaxed">
          {entries.map(([k, v], i) => (
            <span key={k}>
              {i > 0 && <span className="text-dp-text-muted mx-1">·</span>}
              <span className="text-dp-text-muted">{formatHeaderLabel(k)}:</span>{' '}
              <span className="text-dp-text">{String(v)}</span>
            </span>
          ))}
        </span>
      );
    }

    // ── Array ──
    if (Array.isArray(value)) {
      if (value.length === 0) return <span className="text-dp-text-muted select-none">—</span>;
      const formatted = formatArray(value);
      return (
        <span className="text-dp-text text-xs leading-relaxed" title={formatted}>
          {formatted}
        </span>
      );
    }

    // From here, value is a primitive (string/number)
    const strValue = String(value);

    // ── Currency type from schema ──
    if (fieldType === 'currency' || fieldType === 'money') {
      const num = Number(value);
      if (!isNaN(num)) {
        return <span className="font-medium text-dp-text tabular-nums">{formatNumber(num)}</span>;
      }
    }

    // ── Number type from schema, or actual number ──
    if (typeof value === 'number' || fieldType === 'number' || fieldType === 'integer' || fieldType === 'float') {
      const num = Number(value);
      if (!isNaN(num)) {
        // Check if this is a year-like number (1900-2099) in a date/year context
        if ((colLower.includes('year') || colLower.includes('founded') || fieldType === 'year') 
            && num >= 1900 && num <= 2099) {
          return <span className="text-dp-text tabular-nums">{Math.floor(num)}</span>;
        }
        return <span className="text-dp-text tabular-nums">{formatNumber(num)}</span>;
      }
    }

    // ── URL type from schema or detected ──
    if (fieldType === 'url' || colLower.includes('url') || colLower.includes('website') || 
        colLower.includes('link') || isUrlString(strValue)) {
      if (isUrlString(strValue)) {
        return (
          <a 
            href={strValue} 
            target="_blank" 
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1.5 text-dp-accent hover:text-dp-accent-hover transition-colors font-medium text-xs group"
            title={strValue}
          >
            <span className="truncate max-w-[140px]">{shortenUrl(strValue)}</span>
            <ExternalLink className="w-3 h-3 shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
          </a>
        );
      }
    }

    // ── Date type from schema or detected ──
    if (fieldType === 'date' || fieldType === 'datetime' || fieldType === 'timestamp' || isIsoDate(strValue)) {
      const dateFormatted = formatDate(value);
      if (dateFormatted) {
        return <span className="text-dp-text-secondary text-xs tabular-nums">{dateFormatted}</span>;
      }
    }

    // ── Default: plain string ──
    return (
      <span className="text-dp-text" title={strValue.length > 40 ? strValue : undefined}>
        {strValue.length > 60 ? strValue.slice(0, 57) + '…' : strValue}
      </span>
    );
  };

  return (
    <Card variant="bordered" padding="none" className="overflow-hidden flex flex-col bg-dp-bg-raised min-w-0">
      
      {/* ── Toolbar ── */}
      <div className="p-4 border-b border-dp-border flex flex-wrap items-center justify-between gap-3">
        
        {/* Search & Dynamic Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <Input 
            icon={<Search className="w-4 h-4" />}
            placeholder="Search all dataset records..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            fullWidth={false}
            className="w-full sm:w-64"
          />
          
          {filterableFields.length > 0 && (
            <div className="flex items-center gap-2">
              <Select 
                value={selectedFilterField}
                onChange={(e) => {
                  setSelectedFilterField(e.target.value);
                  setSelectedFilterValue('All');
                  setCurrentPage(1);
                }}
                fullWidth={false}
                className="w-36"
              >
                <option value="All">Filter Field</option>
                {filterableFields.map(field => (
                  <option key={field} value={field}>{formatHeaderLabel(field)}</option>
                ))}
              </Select>

              {selectedFilterField !== 'All' && (
                <Select 
                  value={selectedFilterValue}
                  onChange={(e) => {
                    setSelectedFilterValue(e.target.value);
                    setCurrentPage(1);
                  }}
                  fullWidth={false}
                  className="w-36"
                >
                  <option value="All">All Values</option>
                  {filterOptions.map(val => (
                    <option key={val} value={val}>{val}</option>
                  ))}
                </Select>
              )}
            </div>
          )}
        </div>

        {/* Export & Actions */}
        <div className="flex items-center gap-3 flex-wrap">
          {onAddRecord && (
            <Button 
              variant="outline" 
              size="sm" 
              icon={<Plus className="w-4 h-4" />}
              onClick={() => setShowAddModal(true)}
            >
              Add Record
            </Button>
          )}

          {/* Export CSV */}
          <Button 
            variant="primary" 
            size="sm" 
            icon={exportingFormat === 'csv' ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : exportSuccess?.includes('CSV') ? <Check className="w-4 h-4" /> : <FileSpreadsheet className="w-4 h-4" />} 
            onClick={() => handleExport('csv')}
            loading={exportingFormat === 'csv'}
            disabled={filteredData.length === 0}
          >
            Export CSV
          </Button>

          {/* Export JSON */}
          <Button 
            variant="outline" 
            size="sm" 
            icon={exportingFormat === 'json' ? <div className="w-4 h-4 border-2 border-dp-accent border-t-transparent rounded-full animate-spin" /> : exportSuccess?.includes('JSON') ? <Check className="w-4 h-4 text-dp-success" /> : <FileJson className="w-4 h-4" />} 
            onClick={() => handleExport('json')}
            loading={exportingFormat === 'json'}
            disabled={filteredData.length === 0}
          >
            Export JSON
          </Button>
        </div>
      </div>

      {/* ── Notifications / Error Banners ── */}
      {exportSuccess && (
        <div className="bg-dp-success/10 border-b border-dp-success/20 text-dp-success text-xs px-4 py-2 flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>{exportSuccess}</span>
        </div>
      )}
      {exportError && (
        <div className="bg-dp-error/10 border-b border-dp-error/20 text-dp-error text-xs px-4 py-2 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{exportError}</span>
        </div>
      )}

      {/* ── Table Container with horizontal scroll ── */}
      <div className="overflow-x-auto w-full min-w-0 max-w-full">
        <table className="w-full text-sm text-left" style={{ minWidth: columns.length > 4 ? `${columns.length * 160 + 140}px` : undefined }}>
          <thead className="bg-dp-bg-surface text-dp-text-muted text-xs uppercase border-b border-dp-border">
            <tr>
              <th className="px-4 py-3.5 font-medium w-12 whitespace-nowrap">
                <Checkbox 
                  checked={selectedRows.size === paginatedData.length && paginatedData.length > 0}
                  onChange={handleSelectAll}
                />
              </th>
              {columns.map(col => (
                <th 
                  key={col} 
                  className={cn(
                    "px-4 py-3.5 font-semibold cursor-pointer hover:text-dp-text transition-colors whitespace-nowrap tracking-wider",
                    getColumnMinWidth(col, schemaTypeMap[col])
                  )}
                  onClick={() => handleSort(col)}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{formatHeaderLabel(col)}</span>
                    {sortConfig.key === col && <ArrowDownUp className="w-3 h-3 text-dp-accent shrink-0" />}
                  </div>
                </th>
              ))}
              <th className="px-4 py-3.5 font-semibold text-right whitespace-nowrap w-24 sticky right-0 bg-dp-bg-surface z-10">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dp-border">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length + 2} className="px-4 py-12 text-center text-dp-text-muted">
                  Loading dataset records...
                </td>
              </tr>
            ) : paginatedData.length > 0 ? (
              paginatedData.map((row) => (
                <tr 
                  key={row.id} 
                  onClick={() => setViewingRecord(row)}
                  className={cn(
                    "transition-colors cursor-pointer",
                    selectedRows.has(row.id) ? "bg-dp-accent/5" : "hover:bg-dp-bg-hover/50"
                  )}
                >
                  <td className="px-4 py-3.5" onClick={(e) => e.stopPropagation()}>
                    <Checkbox 
                      checked={selectedRows.has(row.id)}
                      onChange={() => handleSelectRow(row.id)}
                    />
                  </td>
                  {columns.map(col => (
                    <td 
                      key={col} 
                      className={cn(
                        "px-4 py-3.5 text-dp-text font-normal whitespace-nowrap",
                        getColumnMinWidth(col, schemaTypeMap[col])
                      )}
                    >
                      {renderCellContent(row.data?.[col], col)}
                    </td>
                  ))}
                  <td className="px-4 py-3.5 text-right sticky right-0 bg-dp-bg-raised z-10" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-end gap-1.5">
                      <button
                        onClick={() => setViewingRecord(row)}
                        className="p-1.5 rounded-md text-dp-text-muted hover:text-dp-accent hover:bg-dp-bg-surface transition-colors cursor-pointer"
                        title="View Record Details"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {onDeleteRecord && (
                        <button 
                          onClick={() => onDeleteRecord(row.id)} 
                          className="p-1.5 rounded-md text-dp-text-muted hover:text-dp-error hover:bg-dp-bg-surface transition-colors cursor-pointer"
                          title="Delete Record"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length + 2} className="px-4 py-12 text-center text-dp-text-muted">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <AlertCircle className="w-8 h-8 text-dp-text-muted/60" />
                    <p className="font-medium text-dp-text-secondary">No records found matching your criteria.</p>
                    <p className="text-xs text-dp-text-muted">Try clearing your search query or filters.</p>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ── Pagination ── */}
      <div className="p-4 border-t border-dp-border flex flex-wrap items-center justify-between gap-3 bg-dp-bg-surface/50">
        <div className="text-sm text-dp-text-secondary">
          Showing <span className="font-medium text-dp-text">{filteredData.length > 0 ? (currentPage - 1) * rowsPerPage + 1 : 0}</span> to <span className="font-medium text-dp-text">{Math.min(currentPage * rowsPerPage, filteredData.length)}</span> of <span className="font-medium text-dp-text">{filteredData.length}</span> records
        </div>
        
        <div className="flex items-center gap-2">
          <Button 
            variant="outline" 
            size="sm" 
            icon={<ChevronLeft className="w-4 h-4" />} 
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
          />
          <div className="text-sm text-dp-text-secondary px-2">
            Page {currentPage} of {totalPages || 1}
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            icon={<ChevronRight className="w-4 h-4" />} 
            disabled={currentPage >= totalPages || totalPages === 0}
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
          />
        </div>
      </div>

      {/* ── Add Record Modal ── */}
      {showAddModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setShowAddModal(false)}>
          <div className="bg-dp-bg-raised border border-dp-border rounded-[var(--radius-card)] p-6 max-w-lg w-full shadow-2xl space-y-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-dp-text">Add Record to {datasetName}</h3>
            <form onSubmit={handleCreateRecordSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
              {columns.map(col => (
                <div key={col} className="space-y-1">
                  <label className="text-xs font-semibold text-dp-text-secondary">{formatHeaderLabel(col)}</label>
                  <Input 
                    placeholder={`Enter ${formatHeaderLabel(col)}...`}
                    value={newRecordData[col] || ''}
                    onChange={(e) => setNewRecordData({ ...newRecordData, [col]: e.target.value })}
                  />
                </div>
              ))}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-dp-border">
                <Button variant="ghost" size="sm" type="button" onClick={() => setShowAddModal(false)}>Cancel</Button>
                <Button size="sm" type="submit" loading={isSubmittingRecord}>Save Record</Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── View Record Details Modal ── */}
      {viewingRecord && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" onClick={() => setViewingRecord(null)}>
          <div className="bg-dp-bg-raised border border-dp-border rounded-[var(--radius-card)] p-6 max-w-2xl w-full shadow-2xl space-y-4 max-h-[85vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-dp-border pb-3">
              <div>
                <h3 className="text-lg font-bold text-dp-text">Record Details</h3>
                <p className="text-xs text-dp-text-muted mt-0.5">Record ID: {viewingRecord.id}</p>
              </div>
              <button onClick={() => setViewingRecord(null)} className="p-1 text-dp-text-muted hover:text-dp-text">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="overflow-y-auto flex-1 space-y-4 pr-1">
              <div className="space-y-3">
                {Object.entries(viewingRecord.data || viewingRecord).map(([key, val]) => (
                  <div key={key} className="p-3 rounded-lg bg-dp-bg-surface border border-dp-border/60 flex flex-col gap-1">
                    <span className="text-xs font-semibold uppercase text-dp-text-muted tracking-wider">
                      {formatHeaderLabel(key)}
                    </span>
                    <span className="text-sm font-medium text-dp-text break-all">
                      {renderCellContent(val, key)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="border-t border-dp-border pt-3 flex items-center justify-end">
              <Button variant="outline" size="sm" onClick={() => setViewingRecord(null)}>Close</Button>
            </div>
          </div>
        </div>
      )}

    </Card>
  );
};
