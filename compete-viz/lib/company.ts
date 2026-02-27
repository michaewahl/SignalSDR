import config from "@/company.json";

export interface CompanyIdentity {
  name: string;
  shortName: string;
}

const company: CompanyIdentity = config;

export function getCompanyName(): string {
  return company.name;
}

export function getShortName(): string {
  return company.shortName;
}
