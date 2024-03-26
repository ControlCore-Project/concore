import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;


public class concore{

    /*decided to proceed with declaring s and olds as Strings for ease of working in the read method and in java a char can't
    absolutely blank one must add the /0 into it to indicate null*/
    private static String s = "";
    private static String olds = "";
    private static String inpath = "./in";
    private static String outpath = "./out";
    //Time in java is in milliseconds
    public static int delay = 1000;
    public static int retryCount = 0;
    public static double simTime;
    Map<String, Integer> oport;
    Map<String, Integer> iport;
    public static Map<String, Integer> params = new HashMap<>();
    public static int maxtime;

static{
   params = initializeSparams();
}

//used the constructor to call the parser method for iport and oport
public concore(){
    iport = mapParser("concore.iport");

    oport = mapParser("concore.oport");
}

//Kill task for windows
public void checkOS(){
    String osName = System.getProperty("os.name");
    long processID = ProcessHandle.current().pid();
    String batContent = "taskill /F /PID "+processID;

    if(osName.toLowerCase().contains("windows")){
        try{
            Files.write(Paths.get("concore.bat"), batContent.getBytes(StandardCharsets.UTF_8));
    } catch(IOException e) {
        e.printStackTrace();
    }
}
}

//parser method which would parse for iport and oport
public static Map<String, Integer> mapParser(String fileName) {

    Map<String, Integer> ans = new HashMap<>();
    

    try{
        BufferedReader portFileReader = new BufferedReader(new FileReader(fileName));
        String fileLine;

       while ((fileLine= portFileReader.readLine())!= null){
        int colonIndex = fileLine.indexOf(':');

        if(colonIndex!= -1){
            String key = fileLine.substring(0, colonIndex).trim();
            int value = Integer.parseInt(fileLine.substring(colonIndex + 1));
         ans.put(key, value);    
        } 
    };
            portFileReader.close();

    } catch(IOException e){
      e.printStackTrace();
    }
    return ans;
}

public static Map<String, Integer> initializeSparams(){
    
    int value;
    
    try {
        
        String originalSparams = Files.readString(Paths.get(inpath+"1/concore.params"));
        String sparams = null;

        //if the os is windows which keeps ""
        if (originalSparams.startsWith("\"")){

           sparams = originalSparams.substring(1, originalSparams.indexOf("\"", 1));
        } else{
            originalSparams = sparams;
        };

        //checks for uncoverted sparams, if present it converts them into an array then places it keys and values into a hashmap
        if (sparams.contains("{")==false){
           System.out.println("converting sparams: "+sparams);
           String[] sparamsArray = sparams.split(";");
             
             for(int i=0; i<sparamsArray.length; i++){
                String[] keyAndValue =  sparamsArray[i].split("=");

                value = Integer.parseInt(keyAndValue[1]);
                 params.put(keyAndValue[0], value);
                  System.out.println("Converted sparams: "+params);
        //no need to convert to a dict since they are already in the map        
             }
           }
        

    } catch (Exception e) {
        e.printStackTrace();
    }

    return params;
}

public int typeparams(String n, int i){
    try{
        return params.get(n);
      
    }catch(Exception e){

        return i;
    }
}

public static void defaultMaxtime(int defaulTime){
    try{
        String max = Files.readString(Paths.get(inpath+"1/concore.maxtime"));
        maxtime = Integer.parseInt(max);

    }catch(Exception e){
       maxtime = defaulTime;
       
    }

}

public static boolean unchanged(){
  if(olds==s){
    s="";
    return true;
  } else {
    olds=s;
    return false;
  }
}

public static String read(int port, String name, String initStr){
try{
    Thread.sleep(delay);

} catch(InterruptedException e){
  e.printStackTrace();
}
String ins;
try{
    ins = Files.readString(Paths.get(inpath+String.valueOf(port)+"/"+name)); 
}catch(IOException e){
    ins = initStr;
} 

while(ins.length()==0){
    try{
        Thread.sleep(delay);
    } catch(InterruptedException e){
        e.printStackTrace();
    }

    try{
        ins = Files.readString(Paths.get(inpath+String.valueOf(port)+"/"+name));
    } catch(IOException e){
        e.printStackTrace();
    }
    retryCount ++;

}
s += ins;


//Used the java regex matcher to find the first digit in the String inval since Java doesn't have literal_eval
Matcher numMatcher = Pattern.compile("\\^d+").matcher(ins);
int sTime = 0;
if(numMatcher.find()){
  sTime = Integer.parseInt(numMatcher.group());
}

simTime = Math.max(simTime, sTime);

String[] inval = ins.split("\\d+", 2);
return inval[1];
}

public static void write(int port, String name, Object val, int delta){
    if(val instanceof String){
        try{
            Thread.sleep(delay);
        } catch(InterruptedException e){
            e.printStackTrace();
        }
    }else if(val instanceof List){
        System.out.println("mywrite must have list or string");
        return;
    }

    try(FileWriter outfile = new FileWriter(outpath+String.valueOf(port)+"/"+name)){
        if (val instanceof List){
            //due to runtime type erasure, we would have to cast val
           @SuppressWarnings("unchecked")
           List<Object>listVal = (List<Object>)val;
           listVal.add(0, simTime+delta);
           outfile.write(listVal.toString());
           simTime += delta;

        } else{
            outfile.write(val.toString());
        }
    }catch(IOException e){
        System.out.println("skipping"+outpath+String.valueOf(port)+"/"+name);
    }
}

public static String initval(String simtimeVal){
Matcher valMatcher = Pattern.compile("\\^d+").matcher(simtimeVal);

List<String> val = new ArrayList<>();

if(valMatcher.find()){
val.add(valMatcher.group());

val.add(simtimeVal.substring(valMatcher.end()));

}
simTime = Integer.parseInt(val.get(0));

return val.get(1);
}
public static void main(String[] args){
 
    defaultMaxtime(100);
    unchanged();
}
}
