The data model
==============

Zoo example
-----------

Conceptual idea for using xdapy:

1) save a whole scene not only single events
2) separate scene in hierarchical relations 
3) supplement other informations to be attached to that hierarchy.
4) turn into xdapy structures. 

To illustrate the idea with an example from outside experimental science, think of a zoo. 
This zoo has animals from two continents, Africa and Australia, and six species. 
For each continent a specific house was build. The African building contains lions, giraffes, zebras and hippos. 
The Australian house koala bears and kangaroos. Maria, the zoo manager employs two zookeepers, Susan and Stefan. 
To keep track of the animal a zoo database is created. 
Susan and Stefan can use the database for example to estimate the amount of food they need to order or 
to keep track of the animals' health records. 

1)
To save all the information about the zoo, we first determine the properties of the zoo, for example its opening hours, its animals and . 
These properties cluster into logical groups which we isolate and label with a name. 
Here, the clusters could be called: zoo for very general informations,
buildings for the two animal houses, species for a species' general properties, animal for the distinct properties of one specific animal and person for the information about the people working at the zoo.
This is a possible list of clusters for the zoo example with their label and properties.

=============  	============  
zoo       
=============  	============
opening hours	9.00h-18.00h
city			Berlin
=============  	============


===========  ===========
building		
===========  ===========
continent	 Africa
temperature	 28 degree C
area		 2 ha
===========  =========== 


============  =========  ==========  ==========  ==========
species	
============  =========  ==========  ==========	 ==========
type          Lion       Giraffe     Kangaroos   Koala bear
diet          carnivore  vegetarian  vegetarian  vegetarian
foot demand   4 kg       2 kg        1 kg        0.5 kg
water demand  1 l        3 l         1 l         0.8 l
============  =========  ==========  ==========	 ==========



=============  	=============   ==============  =============  	=============
animal		
=============  	=============   ==============  =============  	=============
name            Zumba           Kula            ...             ...
weight          1000kg          50kg
birthday        12.03.1995      06.07.2008
birthplace      Serengeti       Ayers Rock
gender          male            female
=============  	=============   ============== 	=============  	=============



=============  	=============   ============== 	==============
person
=============  	=============   ============== 	==============
name            Susan           Stefan          Maria
job             zookeeper       zookeeper       manager
birthyear       1983            1976            1973
gender          female          male            female
=============  	=============   ============== 	==============

2)
Next we determine a hierarchical order of the clusters:

zoo					
|					
house				
|					
species				
|					
animal	

The tree that results from that hierarchy looks like this:

Berlin zoo
|					\
Africa building		Australia building
|		\			|		\
Lion	Giraffe		Koala	Kangaroos
|					|
Zumba				Kula
	



zoo					Berlin zoo
|					|					\
house				Africa building		Australia building
|					|		\			|		\
species				Lion	Giraffe		Koala	Kangaroos
|					|					|
animal				Zumba				Kula

3)
The hierarchy is missing the persons that work at the zoo.
Susan is responsible for the lions and koalas and Stefan for giraffes and kangaroos.
The zookeepers can not simply be incorporated into the hierarchy. 
Wherever we were to put them in the hierarchy, they would occur repeatedly.
That is why we attach them to the hierarchy at the level they would occur. 
As our zookeepers are responsible for several species, the manager is responsible for the whole zoo. 
 
zoo	-- manager			
|					
house				
|					
species	-- keeper			
|					
animal				
	
4) 
After having isolated the critical clusters and properties, we would have to turn them into structures that Xdapy understands. 
How Xdapy represents the clusters will be explained in the next section with a second example. 
There we will be more concrete and provide Python code and technical remarks. 


Science example
---------------


How can all the data about an experiment including
annotations be structured? To approach this
question we will inspect a typical visual psychophysics experiment. 
An observer sits in front of a monitor
and holds a response box in her hands. A stimulus is presented 
on the screen and depending on the task, the observer
presses a button. A computer controls stimulus presentation
as well as response registration. This scene is part of a larger
context. The observer participates in a full experiment which
probably requires that the person observes several sessions
likely at different days. During a session the observer sees
many stimuli and a single repetition of stimulus presentation
with response is called a trial. For subsequent analysis, all
information present in the scene should be stored as annotations
in addition to the data. Temporal, material, or logical
units—such as the observer, the equipment, the experimental
design, a specific session, or a single trial—implicitly divide
annotations and data into clusters. The objects emerge out
of these clusters. Moreover, most experiments have an inherent,
hierarchical structure. A trial, for example, belongs to a
session within an experiment. 
