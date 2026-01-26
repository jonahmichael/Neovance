"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Edit } from "lucide-react";

interface BabyProfile {
  mrn: string;
  full_name: string;
  sex: string;
  dob: string;
  time_of_birth: string;
  birth_order: number;
  gestational_age: string;
  apgar_1min: number;
  apgar_5min: number;
  mother_name: string;
  mother_age: number;
  mother_contact: string;
  father_name: string;
  father_contact: string;
  mother_blood_type: string;
  birth_weight: number;
  birth_length: number;
  birth_head_circumference: number;
  birth_chest_circumference: number;
  current_weight: number;
  discharge_weight: number;
  muscle_tone: string;
  reflexes: string;
  alertness: string;
  cry: string;
  skin_color: string;
  fontanelle: string;
  hearing_screen: string;
  vision_screen: string;
  pulse_oximetry: number;
  breathing_pattern: string;
  heart_sounds: string;
  newborn_metabolic_screen: string;
  blood_glucose_level: number;
  bilirubin_level: number;
  infant_blood_type: string;
  vitamin_k: string;
  hepatitis_b_vaccine: string;
  eye_prophylaxis: string;
  feeding_type: string;
  feeding_tolerance: string;
  urine_output: string;
  stool_output: string;
  nicu_admission: boolean;
  oxygen_support: string;
  medications: string;
  medical_procedures: string;
  maternal_infections: string;
  delivery_method: string;
  complications: string;
  discharge_date: string;
  discharge_instructions: string;
  primary_care_pediatrician: string;
  attending_physician: string;
  nursing_staff: string;
  notes: string;
}

interface BabyDetailProps {
  mrn: string;
  onBack: () => void;
}

export default function BabyDetail({ mrn, onBack }: BabyDetailProps) {
  const [baby, setBaby] = useState<BabyProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBabyDetail();
  }, [mrn]);

  const fetchBabyDetail = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/baby/${mrn}`);
      setBaby(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching baby detail:", error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">Loading patient record...</div>
        </CardContent>
      </Card>
    );
  }

  if (!baby) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">Patient record not found</div>
          <Button onClick={onBack} variant="outline" className="mt-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to List
          </Button>
        </CardContent>
      </Card>
    );
  }

  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );

  const Field = ({ label, value }: { label: string; value: any }) => (
    <div className="py-2 border-b border-border last:border-0">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-sm font-medium">{value || "—"}</div>
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button onClick={onBack} variant="outline" size="sm">
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold">{baby.full_name}</h2>
            <div className="text-sm text-muted-foreground">MRN: {baby.mrn}</div>
          </div>
        </div>
        <div className={`px-3 py-1 rounded text-sm ${
          baby.nicu_admission 
            ? "bg-yellow-900/30 text-yellow-400 border border-yellow-900"
            : "bg-green-900/30 text-green-400 border border-green-900"
        }`}>
          {baby.nicu_admission ? "NICU" : "Ward"}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Section title="Identification">
          <Field label="Full Name" value={baby.full_name} />
          <Field label="Medical Record Number" value={baby.mrn} />
          <Field label="Sex" value={baby.sex} />
          <Field label="Date of Birth" value={new Date(baby.dob).toLocaleDateString()} />
          <Field label="Time of Birth" value={baby.time_of_birth} />
          <Field label="Birth Order" value={baby.birth_order} />
        </Section>

        <Section title="Birth Information">
          <Field label="Gestational Age" value={baby.gestational_age} />
          <Field label="Apgar Score (1 min)" value={`${baby.apgar_1min}/10`} />
          <Field label="Apgar Score (5 min)" value={`${baby.apgar_5min}/10`} />
          <Field label="Delivery Method" value={baby.delivery_method} />
          <Field label="Complications" value={baby.complications} />
        </Section>

        <Section title="Parents Information">
          <Field label="Mother's Name" value={baby.mother_name} />
          <Field label="Mother's Age" value={baby.mother_age} />
          <Field label="Mother's Contact" value={baby.mother_contact} />
          <Field label="Mother's Blood Type" value={baby.mother_blood_type} />
          <Field label="Father's Name" value={baby.father_name} />
          <Field label="Father's Contact" value={baby.father_contact} />
          <Field label="Maternal Infections" value={baby.maternal_infections} />
        </Section>

        <Section title="Measurements">
          <Field label="Birth Weight" value={`${baby.birth_weight} kg`} />
          <Field label="Birth Length" value={`${baby.birth_length} cm`} />
          <Field label="Birth Head Circumference" value={`${baby.birth_head_circumference} cm`} />
          <Field label="Birth Chest Circumference" value={`${baby.birth_chest_circumference} cm`} />
          <Field label="Current Weight" value={`${baby.current_weight} kg`} />
          <Field label="Discharge Weight" value={baby.discharge_weight ? `${baby.discharge_weight} kg` : "—"} />
        </Section>

        <Section title="Physical Examination">
          <Field label="Muscle Tone" value={baby.muscle_tone} />
          <Field label="Reflexes" value={baby.reflexes} />
          <Field label="Alertness" value={baby.alertness} />
          <Field label="Cry" value={baby.cry} />
          <Field label="Skin Color" value={baby.skin_color} />
          <Field label="Fontanelle" value={baby.fontanelle} />
        </Section>

        <Section title="Sensory Screening">
          <Field label="Hearing Screen" value={baby.hearing_screen} />
          <Field label="Vision Screen" value={baby.vision_screen} />
        </Section>

        <Section title="Cardiorespiratory">
          <Field label="Pulse Oximetry" value={`${baby.pulse_oximetry}%`} />
          <Field label="Breathing Pattern" value={baby.breathing_pattern} />
          <Field label="Heart Sounds" value={baby.heart_sounds} />
        </Section>

        <Section title="Laboratory Results">
          <Field label="Newborn Metabolic Screen" value={baby.newborn_metabolic_screen} />
          <Field label="Blood Glucose Level" value={`${baby.blood_glucose_level} mg/dL`} />
          <Field label="Bilirubin Level" value={`${baby.bilirubin_level} mg/dL`} />
          <Field label="Infant Blood Type" value={baby.infant_blood_type} />
        </Section>

        <Section title="Immunizations">
          <Field label="Vitamin K" value={baby.vitamin_k} />
          <Field label="Hepatitis B Vaccine" value={baby.hepatitis_b_vaccine} />
          <Field label="Eye Prophylaxis" value={baby.eye_prophylaxis} />
        </Section>

        <Section title="Feeding & Output">
          <Field label="Feeding Type" value={baby.feeding_type} />
          <Field label="Feeding Tolerance" value={baby.feeding_tolerance} />
          <Field label="Urine Output" value={baby.urine_output} />
          <Field label="Stool Output" value={baby.stool_output} />
        </Section>

        <Section title="Clinical Course">
          <Field label="NICU Admission" value={baby.nicu_admission ? "Yes" : "No"} />
          <Field label="Oxygen Support" value={baby.oxygen_support} />
          <Field label="Medications" value={baby.medications} />
          <Field label="Medical Procedures" value={baby.medical_procedures} />
        </Section>

        <Section title="Care Team">
          <Field label="Attending Physician" value={baby.attending_physician} />
          <Field label="Primary Care Pediatrician" value={baby.primary_care_pediatrician} />
          <Field label="Nursing Staff" value={baby.nursing_staff} />
        </Section>

        <Section title="Discharge Information">
          <Field label="Discharge Date" value={baby.discharge_date ? new Date(baby.discharge_date).toLocaleDateString() : "—"} />
          <Field label="Discharge Instructions" value={baby.discharge_instructions} />
        </Section>

        <Section title="Clinical Notes">
          <div className="text-sm whitespace-pre-wrap">{baby.notes || "—"}</div>
        </Section>
      </div>
    </div>
  );
}
