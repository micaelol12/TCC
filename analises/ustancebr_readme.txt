#####################################
UstanceBR r2 and r3 version corpora
#####################################


Camila Farias Pena Pereira
Matheus Camasmie Pavan  
Sungwon Yoon 
Ricelli Moreira Silva Ramos 
Pablo Botton da Costa 
Laís Carraro Leme Cavalheiro        
Ivandré Paraboni


School of Arts, Sciences and HUmanities (EACH)
University of São Paulo (USP)
São Paulo, Brazil


This work has been supported by FAPESP grant # 2021/08213-0. 
This work was carried out at the Center for Artificial 
Intelligence (C4AI-USP), with support by the São Paulo 
Research Foundation (FAPESP grant #2019/07665-4) 
and by the IBM Corporation.




This work is licensed under a Creative Commons Attribution 4.0 
International License, and it is free for reuse.


########################################


(PORTUGUES) Esta base de dados reproduz conteúdo disponibilizado publicamente na plataforma Twitter na forma de listas de identificadores de tweets rotuladas com informações de posicionamento (stance) favoráveis e contrários a diferentes tópicos (presidentes brasileiros, medidas relativas ao Covid-19 e instituições). Caso você seja autor de algum destes tweets e não queira que este material seja reutilizado para pesquisa na área de computação e afins, sugere-se remover ou proteger suas publicações para que não sejam mais publicamente acessíveis. 


(ENGLISH) This corpus reproduces data made publicly available on Twitter as lists of tweet IDs and associated labels representing a stance for/against different topics (Brazilian presidents, Covid-19 related measures, and institutions.) If you are the author of any of these tweets and you do not wish them to be reused for research in computer science and related fields, please consider deleting or protecting your posts so that they are no longer publicly available.




#####################################################################
Version r2 - November 2022 (initial, class-balanced train-test split with repeated users)
#####################################################################


The UstanceBR corpus is intended to support NLP research in the Portuguese language in tasks such as stance classification and language generation. The corpus conveys a collection of tweets manually labelled by at least two judges with for/against stance information towards six topics in three general categories: Brazilian presidents (Bolsonaro and Lula), Covid-19-related measures (Hydroxychloroquine and Sinovac vaccine), and institutions (Globo TV Network and church.) The initial letters in the filenames indicate the relevant target (bo and lu, cl and co, and gl and ig, respectively). 


######################################################################
Version r3 - May 2024 (new, unbalanced train-test split with disjoint train and test users)
######################################################################


The r2 corpus version is class-balanced, but it may convey stances published by the same individuals in both train and test sets. Whilst this is not a major concern for standard stance detection from text (i.e., from statements), it is inappropriate for stance detection from non-text data as the same input (e.g., the list of friends of a given individual) will occur in both train and test sets. For that reason, we released a new (r3) train-test split in which train and test users are disjoint. In doing so, however, the corpus is no longer class-balanced (particularly so for the ‘bo’ topic).




######################################################################
Which version to use?
######################################################################


Other than being presented in a different train-test split, the r3 version is identical to the r2 version (i.e., it conveys exactly the same set of tweets). For pure text-based stance detection, r2 is more convenient as it is class-balanced (although r3 will work as well). For non-text stance detection, however, r3 should be used.




#####################
Download instructions
#####################


In accordance to Twitter/X privacy policies that forbid the reproduction of tweet contents, the stance corpus is provided as sets of (labelled) tweet identifiers or tweet IDs). Thus, using these IDs as a starting point, it is necessary to (i) obtain permission from Twitter/X and (ii) choose an API and write a script to retrieve the actual text. 
For (i), please refer to the current Twitter/X policies.


Regarding (ii), although we are unable to provide code for downloading purposes, we may suggest Tweepy (https://docs.tweepy.org/en/stable/) as a straightforward solution (at least for Python developers). The API provides multiple methods for retrieving tweets and related information based on tweet IDs. For instance, the Tweepy method API.lookup_statuses retrieves batches of up to 100 messages each using one single line of code. 


For further details regarding the Tweepy API, please refer to the above link.






###########
File format
###########


Some files are provided in spreadsheet (.xlsx) format, and others in comma-separated format (CSV). 


The CSV files are to be read using semicolon as a separator, and utf-8-sig encoding. In Python/Pandas, you can use:
df = pd.read_csv("file.csv",sep=';',enconding='utf-8-sig') 




##################
Corpus components
##################


UstanceBR comprises the following components, which are described individually bellow.


(1) stance corpus: a collection of tweets manually labelled with for/against/other labels
(2) timelines corpus: other tweets published by every user who produced a for/against stance
(3) network data (2 files): anonymised lists of friends and followers of every user, timestamps and anonymised mentioned usernames 


-----------------------------------------------
r2- and r3- train-test_split_stance_corpus (stance corpus)
-----------------------------------------------
Manually labelled train and test data for each of the six targets. See above for the difference between the r2 and r3 splits.




---------------------------------------------------
user information and timelines (timelines corpus)
---------------------------------------------------
This is the same data for both r2 and r3 splits, although files are named as “r2”.
User_ID
Id_Pol_Fact        Tweets
Words
Start
End
Gender
TopMentions
User_stances
User_TL
===>r2_bo_1        374_for_no | 383_against_no | 737_against_no | 752_against_no        1050        8358        17/07/2015        12/08/2020        m        ['*others*', 'plmdds_lo', 'flugeljuuh', 'saori_wakimoto', 'meninomilgrau', 'eric_ofensivo', 'bgabraga', 'amytiva', 'gabwtfff', 'oficialludmilla', 'flamengo', 'maah_gda', 'zzgregori', 'ehdaora', 'batgirlx0', 'tiemyy_', 'palestra77', 'pqfasiso', 'senhorjesuss', 'danilogentili', 'teixeiraa_09']


---------------------------------------------------
Friend and follower lists
---------------------------------------------------
This is the same data for both r2 and r3 splits, although files are named as “r2”.
A dataframe conveying, for each corpus user, the number of statuses, friends and followers (all of which provided by the Twitter API at the time of the data collection), and anonymised lists of friends and followers. The anonymised identifiers in both lists are compatible, that is, an identifier X in one list corresponds to the same individual X in another list.
User_ID: the anonymised user identifier
Statuses: the number of statues (tweets) obtained at the time of the data collection
N_Friends: the number of friends at the time of the data collection
N_Followers: the number of followers the data collection
Friends_Anon: anonymised list of friends of every user
Followers_Anon: anonymised list of followers of every user


---------------------------------------------------
Timeline dates and mentioned users
---------------------------------------------------
This is the same data for both r2 and r3 splits, although files are named as “r2”.
A dataframe conveying, for each corpus user, the number of usernames mentioned in their timelines (or contacts), and an anonymised list of such contacts.
User_ID: the anonymised user identifier
N_Contacts: the number of unique usernames mentioned in the user's timeline
Timeline: the list of timestamps that corresponds to the user's timeline listed in the timelines corpus.
Anon_Contacts: an anonymised list of usernames mentioned in the user's timeline. For real usernames, it is necessary to download the actual tweet text from the Twitter API using the Tweet_ID information provided in the timelines corpus.










################
REFERENCE        
################


Should you wish to reuse the corpus data, please cite the following publication:


# if using the earlier r1 corpus version:
@inproceedings{micai2022-pavan,
author={Matheus Camasmie Pavan and Ivandr{\'e} Paraboni},
title={Cross-target Stance Classification as Domain Adaptation},
booktitle={{Advances in Computational Intelligence - MICAI 2022 - Lecture Notes in Artificial Intelligence vol 13612}},
year={2022},
publisher={Springer Nature Switzerland},
address={Cham},
pages={15--25},
doi={10.1007/978-3-031-19493-1\_2}
}


# if using the r2 or r3 corpus versions:
@article{ustancebr,
author={Camila Pereira AND Matheus Pavan AND Sungwon Yoon AND Ricelli Ramos AND Pablo Costa AND La\'is Cavalheiro AND Ivandr\'e Paraboni},
title={{UstanceBR}: a social media language resource for stance prediction},
journal={arXiv:2312.06374},
doi={10.48550/arXiv.2312.06374},
year={2023}
}








################
CONTACT
################


For further information, please feel free to contact the authors:


Ivandré Paraboni
ivandre  @  usp . br
School of Arts, Sciences and Humanities (EACH)