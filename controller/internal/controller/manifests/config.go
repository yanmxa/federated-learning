package manifests

type FederatedLearningServerParams struct {
	Namespace           string
	Name                string
	Image               string
	NumberOfRounds      int
	MinAvailableClients int
	StorageName         string
	StoragePath         string
}

type FederatedLearningClientParams struct {
	ManifestName       string
	ManifestNamespace  string
	ClientJobNamespace string
	ClientJobName      string
	ClientJobImage     string
	ClientDataConfig   string
	ServerAddress      string
}
