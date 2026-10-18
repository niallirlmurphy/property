declare module "virtual:street-links" {
  const links: import("./streetRegistry").StreetLink[];
  export default links;
}

declare module "virtual:development-links" {
  const links: import("./developmentRegistry").DevelopmentLink[];
  export default links;
}
