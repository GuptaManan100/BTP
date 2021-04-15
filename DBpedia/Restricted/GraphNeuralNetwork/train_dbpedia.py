import openke
from openke.config import Trainer, Tester
from openke.module.model import TransE
from openke.module.loss import MarginLoss
from openke.module.strategy import NegativeSampling
from openke.data import TrainDataLoader, TestDataLoader

# dataloader for training
train_dataloader = TrainDataLoader(
	in_path = "../OpenKEfiles/DBpedia/Restricted/",
	nbatches = 1000,
	threads = 8,
	sampling_mode = "normal",
	bern_flag = 1,
	filter_flag = 1,
	neg_ent = 25,
	neg_rel = 0)

# dataloader for test
test_dataloader = TestDataLoader("../OpenKEfiles/DBpedia/Restricted/", "link", type_constrain =False)

# define the model
transe = TransE(
	ent_tot = train_dataloader.get_ent_tot(),
	rel_tot = train_dataloader.get_rel_tot(),
	dim = 200,
	p_norm = 1,
	norm_flag = True)

# test the model
transe.load_checkpoint('../checkpoint/dbpedia/restricted/transe.ckpt')
print("loaded checkpoint")
sava_path =  "../checkpoint/dbpedia/restricted/transe.embedding.vec.json"
transe.save_parameters(sava_path)