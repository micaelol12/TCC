###########################################################
The BRmoral corpus of Moral stances and MFT scores

School of Arts, Sciences and Humanities (EACH)
University of São Paulo (USP)

This work is licensed under a Creative Commons Attribution 4.0 International License, and it is free for reuse.

###########################################################

Version 5.10 - September 2019 (initial release)

###########################################################

The BRmoral corpus is a collection of stances on eight 'moral' issues (gay marriage, gun control, abortion, death penalty, drugs legislation, criminal age, racial quotas, church taxes) represented both as text (in the Brazilian Portuguese language) and as sentiment scores (from 'totally against' to 'totally in favour') provided by crowdsourced participants. The corpus also conveys a range of author profile features (age, gender, education level etc.) and the five MFT scores obtained from MFT questionnaires filled in by each participant, and it is intended to support NLP research in stance recognition, author profiling and MFT classification from text.

The corpus is provided as a single CSV file in which rows represent participants, and conveys self-reported information provided by the participants, and a number of 'classes' computed from the data (e.g., discrete age bracket classes computed from age information etc.), and which are intended to facilitate the use of machine learning methods. Missing values are represented as a 'na' string.

The .csv file provided uses semicolon (;) as a separator.


-----------------------	
INSTANCE IDENTIFICATION	
-----------------------

sid	
a unique identifier for each participant (row)

	
---------
TEXT DATA	
---------

t.gay-marriage...t.church-tax	
the eight individual text opinions about each target topic

concat	
the same eight opinions concatenated as a single text. A blank space separates an opinion from the next.

freetext	
a short text about any free (random) topic, only provided by certain participants. Potentially useful as a baseline for author profiling models.


--------------------------	
AUTHOR PROFILE INFORMATION
--------------------------	

age	
participant's age information

gender	
participant's gender information (m or f)

school	
participant's education level, from 1 (basic) to 4 (postgraduate)

it	
participant's IT background (yes/no)

religion	
participant's degree of religiosity, from 0 (no religious at all) to 4 (highly religious)

politics	
participant's political orientation,  from 0 (extreme left) to 5 (extreme right)

ap.age	
categorical class {a0-23, a24-30, a31-99} computed from the above 'age' information for multiclass author profiling.

ap.school	
categorical class {s012, s3, s4} computed from the above 'school' information for multiclass author profiling.

ap.religion	
categorical class {r0, r12, r34} computed from the above 'religion' information for multiclass author profiling.

ap.politics	
categorical class {p12, p3, p45} computed from the above 'politics' information for multiclass author profiling.


------------------	
STANCE INFORMATION
------------------	

s.gay-marriage...s.church-tax	
stance scores from 0 (totally against) to 5 (totally in favour) to support each text stance (t.gay-marriage...t.church-tax). 

st.gay-marriage...st.church-tax	
categorical classes {against, neutral, for} computed from the above scores; scores 0 and 1 make the 'against' class, scores 2,3 are 'neutral' etc. for multiclass stance classification.


----------------	
MFT INFORMATION	
----------------

care,fairness,loyalty,authority,purity	
participant's five MFT scores as computed from the responses provided to the MFT questionnaire

mf.care..mf.purity
ternary low/high/avg classes representing MFT scores below/above 0.5 standard deviation from the mean, for ternary MFT scores classification. Scores within +/- 0.5 standard deviations from the mean are labelled as "avg".

item1...item32	
participant's answers to each individual item of the MFT questionnaire; item6 and item22 are dummy questions.


----------------	
REFERENCES	
----------------

Should you wish to reuse the BRmoral corpus data, please cite the following publications:

@article{brmoral,
author={Matheus Camasmie Pavan and Vitor Garcia dos Santos and Alex Gwo Jen Lan and Jo\~ao Trevisan Martins and Wesley Ramos dos Santos and Caio Deutsch and Pablo Botton da Costa and Fernando Chiu Hsieh and Ivandr\'e  Paraboni},
year={2020},
title={Morality Classification in Natural Language Text},
journal={{IEEE transactions on Affective Computing}},
doi={10.1109/TAFFC.2020.3034050}
}

@inproceedings{ranlp2019,
author={Wesley Ramos dos Santos and Ivandr\'e Paraboni},
title={Moral Stance Recognition and Polarity Classification from Twitter and Elicited Text},
booktitle={Recents Advances in Natural Language Processing ({RANLP-2019})},
year={2019},
pages={1070--1076},
address={Varna, Bulgaria}
}


----------------	
CONTACT
----------------

For further information, please feel free to contact the authors:

Ivandré Paraboni
ivandre  @  usp . br
School of Arts, Sciences and Humanities (EACH)
University of São Paulo (USP)
São Paulo, Brazil
