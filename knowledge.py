import android, os, pickle, sys
droid = android.Android()
RS		= lambda : droid.recognizeSpeech().result
toast 		= droid.makeToast

#Storage
facts=[]
dbfile=sys.path[0] + '/knowledge.pickle'

save_changes	= lambda : pickle.dump(facts,open(dbfile,'wb'))

if os.path.isfile(dbfile):
	facts	= pickle.load(open(dbfile,'rb'))

def store(s,p,o):
	global facts
	facts.append((s,p,o))
	facts	= list(set(facts))
	save_changes()

#Searches
S,P,O = 0,1,2
just 		= lambda bits, func  	: lambda tuples : [[t[b] for b in bits] for t in func(tuples)]
find_by		= lambda bit 		: lambda term :   [x for x in facts if  x[bit]==term	]
find_any	= lambda term		: [x for x in facts if  term in x			]
find_phrase	= lambda phrase	: [x for x in facts if  x == tuple(phrase.split()) 	]

#Generic UI
def toast_count(result_count,subject):
	if 	result_count == 0:	toast("No Results: %s" % (subject))
	elif 	result_count == 1:	toast("1 Result")
	else:				toast("%s Results" % (str(result_count)))

def show_dialog(title="Knowledge",message=None,Objects=[lambda : droid.dialogSetPositiveButtonText('Okay')]):
	droid.dialogCreateAlert(title,message)
	[x() for x in Objects]
	droid.dialogShow()
	return droid.dialogGetResponse().result

#search automation
def recall(term,func=find_any):
	results	= func(term)
	result_count=len(results)
	toast_count(result_count,term)
	if result_count > 0:
		show_dialog(term,
			'',
		[ lambda : droid.dialogSetItems([' '.join(x) for x in results])]
		)

#remebering
def remember(phrase):
	parts	= phrase.split()
	if len(parts)==3:
		s,p,o = parts[0],parts[1],parts[2]
		store(s,p,o)
		toast(' :: '.join([s,p,o]))
	else:
		toast("Try Again")


def loop_add(terms):
	first_terms=RS()
	if first_terms and len(first_terms.split())==terms:
		first_terms=first_terms.split()
		second_terms=True
		while second_terms:
			second_terms=RS()
			if second_terms:
				second_terms=second_terms.split()
				if len(second_terms) == 2 and terms == 1:
					t=first_terms + second_terms
					store(t[0],t[1],t[2])
				if terms == 2:
					for term in second_terms:
						t=first_terms + [term]
						store(t[0],t[1],t[2])

#deletion
def delete_results(subject,results):
	global facts
	make_sure= show_dialog("Delete'" + subject + "'",'\n'.join([' :: '.join(x) for x in results]),
		[lambda : droid.dialogSetNegativeButtonText('Delete'),
		lambda : droid.dialogSetPositiveButtonText('Cancel')])
	if make_sure.has_key('which') and make_sure['which'] == 'negative':
		for r in results:
			facts.remove(r)
		save_changes()
		toast(' '.join([str(len(results)),'deleted: ',subject]))

def delete(term, func):
	results=func(term)
	toast_count(len(results),term)
	if len(results) > 0 :
		delete_results(term,results)

#dump
def list_all():
	global facts
	toast_count(len(facts),'Knowledge')
	if len(facts) > 0:
		show_dialog("All Knowledge",'',[lambda : droid.dialogSetItems([' '.join([x[0],x[1],x[2]]) for x in facts])])

#menu automation
def decision(alist,title='Knowledge Base'):
	droid.dialogCreateAlert(title)
	options, funcs	= [x[0] for x in alist], [x[1] for x in alist]
	result = show_dialog(title, None, [lambda : droid.dialogSetItems(options)])
	if result.has_key('item'):
		funcs[result['item']]()
		return True
	return False

#menus

add_menu 	= lambda : decision([
	('by Subject',	 		lambda : loop_add(1)),
	('by Subject & Predicate',	lambda : loop_add(2))
],'Add Many')


delete_menu 	= lambda : decision([
	('by Phrase',	 lambda : delete(RS()	,find_phrase	)	),
	('by Any',	 lambda : delete(RS()	,find_any	)	),
	('by Subject',	 lambda : delete(RS()	,find_by(S)	)	),
	('by Predicate', lambda : delete(RS()	,find_by(P)	)	),
	('by Object',	 lambda : delete(RS()	,find_by(O)	)	)
],'Delete')

search_menu 	= lambda : decision([
	('By Any',	lambda : recall(RS() 				 )),
	('by Subject',	lambda : recall(RS()	,just([P,O],find_by(S)	))),
	('by Predicate',lambda : recall(RS()	,just([S,O],find_by(P)	))),
	('by Object',	lambda : recall(RS()	,just([S,P],find_by(O)	)))
],'Search')

organize_menu 	= lambda : decision([
	('Add Many',	add_menu	),
	('Delete',	delete_menu	),
	('View All',	list_all	)
],'Organize')


#main menu
main_menu=[
	('Record',	lambda : remember ( RS() ) 	),
	('Search',	search_menu 		),
	('Organize',	organize_menu		)
]

running = True
while running:
	running = decision(main_menu)

