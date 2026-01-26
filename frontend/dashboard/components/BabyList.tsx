"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Baby, Calendar, Weight, Activity, AlertCircle } from "lucide-react";

interface Baby {
  mrn: string;
  full_name: string;
  sex: string;
  dob: string;
  gestational_age: string;
  birth_weight: number;
  mother_name: string;
  primary_care_pediatrician: string;
  nicu_admission: boolean;
  apgar_5min: number;
}

interface BabyListProps {
  onSelectBaby: (mrn: string) => void;
}

export default function BabyList({ onSelectBaby }: BabyListProps) {
  const [babies, setBabies] = useState<Baby[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBabies();
  }, []);

  const fetchBabies = async () => {
    try {
      const response = await axios.get("http://localhost:8000/babies");
      setBabies(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching babies:", error);
      setLoading(false);
    }
  };

  const getStatusColor = (nicu: boolean) => {
    return nicu ? "text-yellow-400" : "text-green-400";
  };

  const getStatusText = (nicu: boolean) => {
    return nicu ? "NICU" : "Ward";
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardContent className="p-12 text-center">
          <div className="text-muted-foreground">Loading patient records...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">All Patients ({babies.length})</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {babies.map((baby) => (
          <Card
            key={baby.mrn}
            className="hover:bg-muted/50 transition-colors cursor-pointer"
            onClick={() => onSelectBaby(baby.mrn)}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-cyan-900/20">
                    <Baby className="h-5 w-5 text-cyan-400" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{baby.full_name}</CardTitle>
                    <div className="text-sm text-muted-foreground">MRN: {baby.mrn}</div>
                  </div>
                </div>
                <div className={`text-xs px-2 py-1 rounded border ${
                  baby.nicu_admission 
                    ? "bg-yellow-900/30 text-yellow-400 border-yellow-900"
                    : "bg-green-900/30 text-green-400 border-green-900"
                }`}>
                  {getStatusText(baby.nicu_admission)}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-muted-foreground">DOB</div>
                    <div className="font-medium">{new Date(baby.dob).toLocaleDateString()}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-muted-foreground">Gestational Age</div>
                    <div className="font-medium">{baby.gestational_age}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Weight className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-muted-foreground">Birth Weight</div>
                    <div className="font-medium">{baby.birth_weight} kg</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <div className="text-muted-foreground">Apgar (5min)</div>
                    <div className="font-medium">{baby.apgar_5min}/10</div>
                  </div>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-border">
                <div className="text-xs text-muted-foreground">Mother: {baby.mother_name}</div>
                <div className="text-xs text-muted-foreground">Pediatrician: {baby.primary_care_pediatrician}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
