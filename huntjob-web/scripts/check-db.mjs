import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://oonkwgfawfyqtrndshhu.supabase.co";
const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9vbmt3Z2Zhd2Z5cXRybmRzaGh1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDY1OTAwMSwiZXhwIjoyMTAwMjM1MDAxfQ.0lthAleSpXco3PLAtSkHbEdhjZurymCjxxn1vZgHRSU";

const supabase = createClient(supabaseUrl, serviceKey);

async function main() {
  console.log("Checking Supabase tables...");
  
  const tables = ['profiles', 'applications', 'resumes', 'interview_sessions', 'payments'];
  for (const table of tables) {
    const { data, error } = await supabase.from(table).select('count', { count: 'exact', head: true });
    if (error) {
      console.log(`❌ Table '${table}':`, error.message);
    } else {
      console.log(`✅ Table '${table}' exists!`);
    }
  }
}

main();
