"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { 
  User, Baby, Heart, Stethoscope, Eye, Syringe, 
  Utensils, Building2, AlertTriangle, ClipboardCheck, 
  Edit3, Save, X, Clock, Shield, CheckCircle2, XCircle,
  ChevronDown, ChevronRight, FileText
} from "lucide-react";

interface BabyProfile {
  [key: string]: string | number | boolean | null | undefined;
  mrn: string;
  full_name: string;
  sex: string;
  dob: string;
  time_of_birth: string;
  place_of_birth: string;
  birth_order: string;
  hospital_id_band: string;
  footprints_taken: boolean;
  gestational_age: string;
  apgar_1min: number;
  apgar_5min: number;
  apgar_10min: number;
  mother_name: string;
  father_name: string;
  parent_contact: string;
  parent_address: string;
  mother_age: number;
  mother_blood_type: string;
  mother_id: string;
  father_id: string;
  emergency_contact: string;
  birth_weight: number;
  length: number;
  head_circumference: number;
  chest_circumference: number;
  weight_percentile: string;
  length_percentile: string;
  head_percentile: string;
  muscle_tone: string;
  moro_reflex: string;
  rooting_reflex: string;
  sucking_reflex: string;
  grasp_reflex: string;
  stepping_reflex: string;
  alertness_level: string;
  cry_strength: string;
  skin_condition: string;
  birthmarks: string;
  bruising: string;
  fontanelle_status: string;
  eye_exam: string;
  ear_exam: string;
  nose_throat_exam: string;
  genital_exam: string;
  anus_patency: string;
  limb_movement: string;
  spine_check: string;
  hip_check: string;
  hearing_screening: string;
  hearing_screening_date: string;
  vision_screening: string;
  red_reflex_right: string;
  red_reflex_left: string;
  response_to_stimuli: string;
  pulse_oximetry: string;
  pulse_ox_right_hand: number;
  pulse_ox_foot: number;
  breathing_pattern: string;
  lung_sounds: string;
  heart_sounds: string;
  heart_murmur_grade: string;
  metabolic_screening: string;
  metabolic_screening_date: string;
  pku_result: string;
  hypothyroidism_result: string;
  sickle_cell_result: string;
  cystic_fibrosis_result: string;
  blood_glucose: string;
  bilirubin_level: string;
  blood_type: string;
  rh_factor: string;
  coombs_test: string;
  vitamin_k_given: boolean;
  vitamin_k_date: string;
  hep_b_vaccine: boolean;
  hep_b_date: string;
  eye_prophylaxis: boolean;
  eye_prophylaxis_date: string;
  other_vaccines: string;
  feeding_method: string;
  feeding_tolerance: string;
  feeds_per_day: number;
  urine_output: string;
  first_void_time: string;
  stool_output: string;
  meconium_passage_time: string;
  vomiting: string;
  reflux: string;
  bed_assignment: string;
  nicu_admission: boolean;
  nicu_admission_reason: string;
  oxygen_support: string;
  fio2: number;
  iv_fluids: string;
  medications: string;
  antibiotics: string;
  procedures: string;
  monitoring_events: string;
  infection_screening: string;
  maternal_infections: string;
  gbs_status: string;
  maternal_hiv: string;
  maternal_hep_b: string;
  maternal_syphilis: string;
  drug_exposure: string;
  delivery_method: string;
  delivery_complications: string;
  birth_complications: string;
  resuscitation_needed: boolean;
  resuscitation_details: string;
  family_genetic_history: string;
  prenatal_history: string;
  prenatal_care: string;
  discharge_date: string;
  discharge_weight: number;
  discharge_diagnosis: string;
  follow_up_appointments: string;
  parent_education: string;
  home_care_instructions: string;
  screening_results_summary: string;
  primary_care_pediatrician: string;
  attending_physician: string;
  primary_nurse: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

interface EditLogEntry {
  block_index: number;
  timestamp: string;
  user_id: string;
  action: string;
  baby_mrn: string;
  changes: Record<string, { old: string; new: string }>;
  previous_hash: string;
  current_hash: string;
}

interface FieldConfig {
  key: string;
  label: string;
  editable: boolean;
  type: "text" | "number" | "boolean" | "textarea" | "select";
  options?: string[];
}

interface SectionConfig {
  id: string;
  title: string;
  icon: React.ReactNode;
  color: string;
  fields: FieldConfig[];
}

export default function PatientProfile({ mrn = "B001", onUpdate }: { mrn?: string, onUpdate?: () => void }) {
  const { user: authUser } = useAuth();
  const [baby, setBaby] = useState<BabyProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editMode, setEditMode] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<Record<string, string | number | boolean>>({});
  const [saving, setSaving] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["identity", "parent", "measurements"]));
  const [editLog, setEditLog] = useState<EditLogEntry[]>([]);
  const [showEditLog, setShowEditLog] = useState(false);
  
  // Use current user credentials for updates
  const [authCredentials] = useState({ 
    user_id: authUser?.userId || "DR001", 
    password: authUser?.userId === "NS001" ? "password@ns" : "password@dr" 
  });

  const sections: SectionConfig[] = [
    {
      id: "identity",
      title: "Identity Information",
      icon: <User className="h-4 w-4" />,
      color: "text-blue-600",
      fields: [
        { key: "full_name", label: "Full Name", editable: true, type: "text" },
        { key: "mrn", label: "MRN", editable: false, type: "text" },
        { key: "sex", label: "Sex", editable: true, type: "select", options: ["Male", "Female", "Unknown"] },
        { key: "dob", label: "Date of Birth", editable: true, type: "text" },
        { key: "time_of_birth", label: "Time of Birth", editable: true, type: "text" },
        { key: "place_of_birth", label: "Place of Birth", editable: true, type: "text" },
        { key: "birth_order", label: "Birth Order", editable: true, type: "text" },
        { key: "hospital_id_band", label: "Hospital ID Band", editable: true, type: "text" },
        { key: "footprints_taken", label: "Footprints Taken", editable: true, type: "boolean" },
        { key: "blood_type", label: "Blood Type", editable: true, type: "text" },
        { key: "rh_factor", label: "Rh Factor", editable: true, type: "text" },
      ],
    },
    {
      id: "birth",
      title: "Gestational & Birth Data",
      icon: <Baby className="h-4 w-4" />,
      color: "text-pink-600",
      fields: [
        { key: "gestational_age", label: "Gestational Age", editable: true, type: "text" },
        { key: "delivery_method", label: "Delivery Method", editable: true, type: "text" },
        { key: "apgar_1min", label: "APGAR 1 min", editable: true, type: "number" },
        { key: "apgar_5min", label: "APGAR 5 min", editable: true, type: "number" },
        { key: "apgar_10min", label: "APGAR 10 min", editable: true, type: "number" },
        { key: "resuscitation_needed", label: "Resuscitation", editable: true, type: "boolean" },
        { key: "resuscitation_details", label: "Resuscitation Details", editable: true, type: "text" },
        { key: "birth_complications", label: "Birth Complications", editable: true, type: "text" },
      ],
    },
    {
      id: "parent",
      title: "Parent Information",
      icon: <User className="h-4 w-4" />,
      color: "text-indigo-600",
      fields: [
        { key: "mother_name", label: "Mother's Name", editable: true, type: "text" },
        { key: "father_name", label: "Father's Name", editable: true, type: "text" },
        { key: "mother_age", label: "Mother's Age", editable: true, type: "number" },
        { key: "mother_blood_type", label: "Mother's Blood Type", editable: true, type: "text" },
        { key: "mother_id", label: "Mother's ID", editable: true, type: "text" },
        { key: "father_id", label: "Father's ID", editable: true, type: "text" },
        { key: "parent_contact", label: "Contact", editable: true, type: "text" },
        { key: "parent_address", label: "Address", editable: true, type: "text" },
        { key: "emergency_contact", label: "Emergency Contact", editable: true, type: "text" },
      ],
    },
    {
      id: "measurements",
      title: "Birth Measurements",
      icon: <Heart className="h-4 w-4" />,
      color: "text-red-600",
      fields: [
        { key: "birth_weight", label: "Weight (kg)", editable: true, type: "number" },
        { key: "length", label: "Length (cm)", editable: true, type: "number" },
        { key: "head_circumference", label: "Head Circ (cm)", editable: true, type: "number" },
        { key: "chest_circumference", label: "Chest Circ (cm)", editable: true, type: "number" },
        { key: "weight_percentile", label: "Weight %ile", editable: true, type: "text" },
        { key: "length_percentile", label: "Length %ile", editable: true, type: "text" },
        { key: "head_percentile", label: "Head %ile", editable: true, type: "text" },
      ],
    },
    {
      id: "physical",
      title: "Physical Examination",
      icon: <Stethoscope className="h-4 w-4" />,
      color: "text-green-600",
      fields: [
        { key: "muscle_tone", label: "Muscle Tone", editable: true, type: "select", options: ["Normal", "Hypotonic", "Hypertonic", "-"] },
        { key: "alertness_level", label: "Alertness", editable: true, type: "select", options: ["Alert", "Drowsy", "Lethargic", "-"] },
        { key: "cry_strength", label: "Cry Strength", editable: true, type: "select", options: ["Strong", "Weak", "Absent", "-"] },
        { key: "moro_reflex", label: "Moro Reflex", editable: true, type: "select", options: ["Present", "Absent", "Weak", "-"] },
        { key: "sucking_reflex", label: "Sucking Reflex", editable: true, type: "select", options: ["Strong", "Weak", "Absent", "-"] },
        { key: "skin_condition", label: "Skin", editable: true, type: "text" },
        { key: "fontanelle_status", label: "Fontanelle", editable: true, type: "select", options: ["Flat", "Bulging", "Sunken", "-"] },
        { key: "hip_check", label: "Hip Screening", editable: true, type: "text" },
      ],
    },
    {
      id: "sensory",
      title: "Sensory Screening",
      icon: <Eye className="h-4 w-4" />,
      color: "text-purple-600",
      fields: [
        { key: "hearing_screening", label: "Hearing", editable: true, type: "select", options: ["Pass", "Refer", "Not Done", "-"] },
        { key: "hearing_screening_date", label: "Hearing Date", editable: true, type: "text" },
        { key: "vision_screening", label: "Vision", editable: true, type: "text" },
        { key: "red_reflex_right", label: "Red Reflex R", editable: true, type: "select", options: ["Present", "Absent", "-"] },
        { key: "red_reflex_left", label: "Red Reflex L", editable: true, type: "select", options: ["Present", "Absent", "-"] },
      ],
    },
    {
      id: "cardio",
      title: "Cardiorespiratory",
      icon: <Heart className="h-4 w-4" />,
      color: "text-red-500",
      fields: [
        { key: "pulse_oximetry", label: "Pulse Ox Result", editable: true, type: "text" },
        { key: "breathing_pattern", label: "Breathing", editable: true, type: "select", options: ["Regular", "Irregular", "Apneic", "-"] },
        { key: "lung_sounds", label: "Lung Sounds", editable: true, type: "select", options: ["Clear", "Crackles", "Wheezing", "-"] },
        { key: "heart_sounds", label: "Heart Sounds", editable: true, type: "text" },
      ],
    },
    {
      id: "lab",
      title: "Laboratory Screening",
      icon: <Syringe className="h-4 w-4" />,
      color: "text-orange-600",
      fields: [
        { key: "metabolic_screening", label: "Metabolic Screen", editable: true, type: "text" },
        { key: "pku_result", label: "PKU", editable: true, type: "select", options: ["Normal", "Abnormal", "Pending", "-"] },
        { key: "hypothyroidism_result", label: "Hypothyroidism", editable: true, type: "select", options: ["Normal", "Abnormal", "Pending", "-"] },
        { key: "sickle_cell_result", label: "Sickle Cell", editable: true, type: "select", options: ["Normal", "Trait", "Disease", "Pending", "-"] },
        { key: "cystic_fibrosis_result", label: "Cystic Fibrosis", editable: true, type: "select", options: ["Normal", "Abnormal", "Pending", "-"] },
        { key: "blood_glucose", label: "Blood Glucose", editable: true, type: "text" },
        { key: "bilirubin_level", label: "Bilirubin", editable: true, type: "text" },
        { key: "coombs_test", label: "Coombs Test", editable: true, type: "select", options: ["Negative", "Positive", "-"] },
      ],
    },
    {
      id: "immunization",
      title: "Immunizations",
      icon: <Syringe className="h-4 w-4" />,
      color: "text-teal-600",
      fields: [
        { key: "vitamin_k_given", label: "Vitamin K", editable: true, type: "boolean" },
        { key: "vitamin_k_date", label: "Vitamin K Date", editable: true, type: "text" },
        { key: "hep_b_vaccine", label: "Hep B Vaccine", editable: true, type: "boolean" },
        { key: "hep_b_date", label: "Hep B Date", editable: true, type: "text" },
        { key: "eye_prophylaxis", label: "Eye Prophylaxis", editable: true, type: "boolean" },
      ],
    },
    {
      id: "feeding",
      title: "Feeding & Elimination",
      icon: <Utensils className="h-4 w-4" />,
      color: "text-yellow-600",
      fields: [
        { key: "feeding_method", label: "Feeding Method", editable: true, type: "select", options: ["Breastfeeding", "Formula", "Mixed", "NPO", "-"] },
        { key: "feeding_tolerance", label: "Tolerance", editable: true, type: "select", options: ["Good", "Poor", "Vomiting", "-"] },
        { key: "urine_output", label: "Urine Output", editable: true, type: "select", options: ["Normal", "Decreased", "Absent", "-"] },
        { key: "stool_output", label: "Stool Output", editable: true, type: "select", options: ["Meconium", "Transitional", "Normal", "-"] },
        { key: "meconium_passage_time", label: "Meconium Time", editable: true, type: "text" },
      ],
    },
    {
      id: "clinical",
      title: "Clinical Course",
      icon: <Building2 className="h-4 w-4" />,
      color: "text-slate-600",
      fields: [
        { key: "bed_assignment", label: "Bed", editable: true, type: "select", options: ["Incubator", "Crib", "Warmer", "-"] },
        { key: "nicu_admission", label: "NICU Admission", editable: true, type: "boolean" },
        { key: "nicu_admission_reason", label: "NICU Reason", editable: true, type: "text" },
        { key: "oxygen_support", label: "O2 Support", editable: true, type: "select", options: ["None", "Nasal Cannula", "CPAP", "Ventilator", "-"] },
        { key: "medications", label: "Medications", editable: true, type: "textarea" },
        { key: "procedures", label: "Procedures", editable: true, type: "textarea" },
      ],
    },
    {
      id: "risk",
      title: "Risk & History",
      icon: <AlertTriangle className="h-4 w-4" />,
      color: "text-amber-600",
      fields: [
        { key: "maternal_infections", label: "Maternal Infections", editable: true, type: "text" },
        { key: "gbs_status", label: "GBS Status", editable: true, type: "select", options: ["Positive", "Negative", "Unknown", "-"] },
        { key: "maternal_hiv", label: "Maternal HIV", editable: true, type: "select", options: ["Positive", "Negative", "Unknown", "-"] },
        { key: "drug_exposure", label: "Drug Exposure", editable: true, type: "text" },
        { key: "prenatal_care", label: "Prenatal Care", editable: true, type: "select", options: ["Adequate", "Inadequate", "None", "-"] },
        { key: "family_genetic_history", label: "Genetic History", editable: true, type: "textarea" },
      ],
    },
    {
      id: "discharge",
      title: "Discharge Data",
      icon: <ClipboardCheck className="h-4 w-4" />,
      color: "text-emerald-600",
      fields: [
        { key: "discharge_date", label: "Discharge Date", editable: true, type: "text" },
        { key: "discharge_weight", label: "Discharge Weight", editable: true, type: "number" },
        { key: "discharge_diagnosis", label: "Diagnosis", editable: true, type: "textarea" },
        { key: "follow_up_appointments", label: "Follow-up", editable: true, type: "textarea" },
        { key: "home_care_instructions", label: "Home Care", editable: true, type: "textarea" },
      ],
    },
    {
      id: "careteam",
      title: "Care Team",
      icon: <Stethoscope className="h-4 w-4" />,
      color: "text-cyan-600",
      fields: [
        { key: "primary_care_pediatrician", label: "Pediatrician", editable: false, type: "text" },
        { key: "attending_physician", label: "Attending", editable: true, type: "text" },
        { key: "primary_nurse", label: "Primary Nurse", editable: true, type: "text" },
      ],
    },
    {
      id: "notes",
      title: "Notes",
      icon: <FileText className="h-4 w-4" />,
      color: "text-gray-600",
      fields: [
        { key: "notes", label: "General Notes", editable: true, type: "textarea" },
      ],
    },
  ];

  useEffect(() => {
    fetchBabyProfile();
    fetchEditLog();
  }, [mrn]);

  const fetchBabyProfile = async () => {
    try {
      const res = await fetch(`http://localhost:8000/baby/${mrn}`);
      const data = await res.json();
      setBaby(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to fetch baby profile:", err);
      setLoading(false);
    }
  };

  const fetchEditLog = async () => {
    try {
      const res = await fetch(`http://localhost:8000/custody-log/${mrn}`);
      if (res.ok) {
        const data = await res.json();
        setEditLog(Array.isArray(data.entries) ? data.entries : Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error("Failed to fetch edit log:", err);
      setEditLog([]);
    }
  };

  const startEdit = (sectionId: string) => {
    if (!baby) return;
    const section = sections.find(s => s.id === sectionId);
    if (!section) return;
    
    const initialValues: Record<string, string | number | boolean> = {};
    section.fields.forEach(field => {
      if (field.editable) {
        const val = baby[field.key];
        initialValues[field.key] = val !== null && val !== undefined ? val : "";
      }
    });
    setEditValues(initialValues);
    setEditMode(sectionId);
  };

  const cancelEdit = () => {
    setEditMode(null);
    setEditValues({});
  };

  const saveEdit = async (sectionId: string) => {
    if (!baby) return;
    setSaving(true);
    
    const section = sections.find(s => s.id === sectionId);
    if (!section) return;
    
    const updates: Record<string, string | number | boolean> = {};
    section.fields.forEach(field => {
      if (field.editable && editValues[field.key] !== undefined) {
        const oldValue = baby[field.key];
        const newValue = editValues[field.key];
        if (String(oldValue) !== String(newValue)) {
          updates[field.key] = newValue;
        }
      }
    });

    if (Object.keys(updates).length === 0) {
      setSaving(false);
      setEditMode(null);
      return;
    }

    try {
      const response = await fetch(`http://localhost:8000/baby/update/${mrn}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          auth: authCredentials,
          updates: updates,
        }),
      });

      if (response.ok) {
        await fetchBabyProfile();
        await fetchEditLog();
        if (onUpdate) onUpdate();
        setEditMode(null);
        setEditValues({});
      }
    } catch (err) {
      console.error("Error saving:", err);
    }
    setSaving(false);
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const renderField = (field: FieldConfig, value: string | number | boolean | null | undefined) => {
    const isEditing = editMode !== null && sections.find(s => s.id === editMode)?.fields.some(f => f.key === field.key);
    
    if (isEditing && field.editable) {
      const editValue = editValues[field.key] ?? value ?? "";
      
      if (field.type === "boolean") {
        return (
          <button
            onClick={() => setEditValues({ ...editValues, [field.key]: !editValue })}
            className={`px-3 py-1 rounded text-sm font-medium ${
              editValue ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
            }`}
          >
            {editValue ? "Yes" : "No"}
          </button>
        );
      }
      
      if (field.type === "select" && field.options) {
        return (
          <select
            value={String(editValue)}
            onChange={(e) => setEditValues({ ...editValues, [field.key]: e.target.value })}
            className="w-full px-2 py-1 border rounded text-sm"
          >
            {field.options.map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      }
      
      if (field.type === "textarea") {
        return (
          <Textarea
            value={String(editValue)}
            onChange={(e) => setEditValues({ ...editValues, [field.key]: e.target.value })}
            className="text-sm"
            rows={2}
          />
        );
      }
      
      return (
        <Input
          type={field.type === "number" ? "number" : "text"}
          value={String(editValue)}
          onChange={(e) => setEditValues({ ...editValues, [field.key]: field.type === "number" ? parseFloat(e.target.value) || 0 : e.target.value })}
          className="text-sm h-8"
        />
      );
    }

    if (field.type === "boolean") {
      return value ? (
        <span className="flex items-center gap-1 text-green-600 text-sm"><CheckCircle2 className="h-4 w-4" /> Yes</span>
      ) : (
        <span className="flex items-center gap-1 text-red-600 text-sm"><XCircle className="h-4 w-4" /> No</span>
      );
    }

    return <span className="text-sm font-medium">{value ?? "-"}</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">Loading patient profile...</div>
      </div>
    );
  }

  if (!baby) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Failed to load patient profile</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{baby.full_name}</h2>
          <p className="text-sm text-muted-foreground">MRN: {baby.mrn} | DOB: {baby.dob}</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowEditLog(!showEditLog)}
          className="flex items-center gap-2"
        >
          <Shield className="h-4 w-4" />
          Chain of Custody ({editLog.length})
        </Button>
      </div>

      {/* Edit Log Panel */}
      {showEditLog && (
        <Card className="bg-slate-50 border-slate-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Shield className="h-4 w-4 text-blue-600" />
              Chain of Custody Audit Trail
            </CardTitle>
          </CardHeader>
          <CardContent>
            {editLog.length === 0 ? (
              <p className="text-sm text-muted-foreground">No changes recorded yet.</p>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {editLog.slice().reverse().map((entry, idx) => (
                  <div key={idx} className="p-3 bg-white rounded border text-xs">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-blue-700">Block #{entry.block_index}</span>
                      <span className="text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p><span className="text-muted-foreground">User:</span> {entry.user_id}</p>
                    <div className="mt-2 p-2 bg-slate-50 rounded text-[10px] font-mono">
                      <p className="truncate">Hash: {entry.current_hash.substring(0, 24)}...</p>
                    </div>
                    {entry.changes && Object.keys(entry.changes).length > 0 && (
                      <div className="mt-2">
                        {Object.entries(entry.changes).map(([key, val]) => (
                          <p key={key}>
                            <span className="font-medium">{key}:</span>{" "}
                            <span className="text-red-600 line-through">{String(val.old)}</span>{" "}
                            <span className="text-green-600">{String(val.new)}</span>
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sections */}
      {sections.map((section) => {
        const isExpanded = expandedSections.has(section.id);
        const isEditing = editMode === section.id;
        const hasEditableFields = section.fields.some(f => f.editable);

        return (
          <Card key={section.id} className="shadow-sm">
            <CardHeader 
              className="py-3 cursor-pointer hover:bg-muted/50 transition-colors"
              onClick={() => toggleSection(section.id)}
            >
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold flex items-center gap-2">
                  <span className={section.color}>{section.icon}</span>
                  {section.title}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {hasEditableFields && isExpanded && !isEditing && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => { e.stopPropagation(); startEdit(section.id); }}
                      className="h-7 px-2"
                    >
                      <Edit3 className="h-3 w-3 mr-1" /> Edit
                    </Button>
                  )}
                  {isEditing && (
                    <>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); cancelEdit(); }}
                        className="h-7 px-2"
                        disabled={saving}
                      >
                        <X className="h-3 w-3 mr-1" /> Cancel
                      </Button>
                      <Button
                        size="sm"
                        onClick={(e) => { e.stopPropagation(); saveEdit(section.id); }}
                        className="h-7 px-2"
                        disabled={saving}
                      >
                        <Save className="h-3 w-3 mr-1" /> {saving ? "..." : "Save"}
                      </Button>
                    </>
                  )}
                  {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
              </div>
            </CardHeader>
            {isExpanded && (
              <CardContent className="pt-0">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {section.fields.map((field) => (
                    <div key={field.key} className="space-y-1">
                      <p className="text-xs text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                        {field.label}
                        {field.editable && <Edit3 className="h-2.5 w-2.5 opacity-50" />}
                      </p>
                      {renderField(field, baby[field.key])}
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        );
      })}

      {/* Footer */}
      <div className="text-center text-xs text-muted-foreground pt-4">
        <p>Last updated: {baby.updated_at ? new Date(baby.updated_at).toLocaleString() : "Unknown"}</p>
        <p className="mt-1">All changes logged with blockchain-style chain of custody</p>
      </div>
    </div>
  );
}
