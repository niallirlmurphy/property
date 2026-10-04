declare module "virtual:street-links" {
  const links: import("./streetRegistry").StreetLink[];
  export default links;
}
