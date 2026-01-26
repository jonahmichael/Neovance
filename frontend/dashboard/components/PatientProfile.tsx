"use client";

import { useEffect, useState } from "react";

interface BabyProfile {
  mrn: string;
  full_name: string;
  sex: string;
  dob: string;
  time_of_birth: string;
  place_of_birth: string;
  birth_order: string;
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
  birth_weight: number;
  length: number;
  head_circumference: number;
  chest_circumference: number;
  delivery_method: string;
  primary_care_pediatrician: string;
  blood_type: string;
}

export default function PatientProfile() {
  const [baby, setBaby] = useState<BabyProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/baby/B001")
      .then((res) => res.json())
      .then((data) => {
        setBaby(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to fetch baby profile:", err);
        setLoading(false);
      });
  }, []);

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

  const sections = [
    {
      title: "Identity Information",
      fields: [
        { label: "Full Name", value: baby.full_name },
        { label: "MRN", value: baby.mrn },
        { label: "Sex", value: baby.sex },
        { label: "Date of Birth", value: baby.dob },
        { label: "Time of Birth", value: baby.time_of_birth },
        { label: "Place of Birth", value: baby.place_of_birth },
        { label: "Birth Order", value: baby.birth_order },
        { label: "Blood Type", value: baby.blood_type },
      ],
    },
    {
      title: "Birth & Gestational Data",
      fields: [
        { label: "Gestational Age", value: baby.gestational_age },
        { label: "Delivery Method", value: baby.delivery_method },
        { label: "APGAR 1 min", value: baby.apgar_1min },
        { label: "APGAR 5 min", value: baby.apgar_5min },
        { label: "APGAR 10 min", value: baby.apgar_10min || "N/A" },
      ],
    },
    {
      title: "Birth Measurements",
      fields: [
        { label: "Birth Weight", value: `${baby.birth_weight} kg` },
        { label: "Length", value: `${baby.length} cm` },
        { label: "Head Circumference", value: `${baby.head_circumference} cm` },
        { label: "Chest Circumference", value: `${baby.chest_circumference} cm` },
      ],
    },
    {
      title: "Parent Information",
      fields: [
        { label: "Mother's Name", value: baby.mother_name },
        { label: "Father's Name", value: baby.father_name },
        { label: "Mother's Age", value: `${baby.mother_age} years` },
        { label: "Mother's Blood Type", value: baby.mother_blood_type },
        { label: "Contact", value: baby.parent_contact },
        { label: "Address", value: baby.parent_address },
      ],
    },
    {
      title: "Care Team",
      fields: [
        { label: "Primary Pediatrician", value: baby.primary_care_pediatrician },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <div key={section.title} className="bg-card rounded-xl p-5 shadow-sm">
          <h3 className="text-lg font-semibold text-primary mb-4 border-b border-border pb-2">
            {section.title}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {section.fields.map((field) => (
              <div key={field.label} className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase tracking-wide">
                  {field.label}
                </p>
                <p className="text-sm font-medium text-foreground">
                  {field.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
