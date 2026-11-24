import aiinterface.CommandCenter;
import com.google.protobuf.Message;
import com.google.protobuf.Descriptors.FieldDescriptor;
import enumerate.BackgroundType;
import fighting.Fighting;
import image.LetterImage;
import input.KeyData;
import loader.ResourceLoader;
import manager.GraphicManager;
import setting.FlagSetting;
import setting.GameSetting;
import setting.LaunchSetting;
import struct.CharacterData;
import struct.FrameData;
import struct.Key;
import util.ResourceDrawer;

import javax.imageio.ImageIO;
import java.awt.Font;
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Locale;
import java.util.Set;

public class CupBridge {
    private static final Set<String> ALLOWED = Set.of(
        "NEUTRAL", "FORWARD_WALK", "DASH", "BACK_STEP", "STAND_GUARD", "CROUCH_GUARD",
        "FOR_JUMP", "STAND_A", "STAND_B", "CROUCH_A", "CROUCH_B",
        "STAND_FA", "STAND_FB", "THROW_A", "STAND_D_DF_FA", "STAND_F_D_DFB"
    );
    private static final Set<String> CHARS = Set.of("ZEN","GARNET","LUD");
    private Fighting fight;
    private int frames, frame, captured, recordEvery;
    private Path capture;
    private BufferedWriter trace;
    private String window = "null";
    private void closeTrace() throws Exception { if(trace!=null){trace.close();trace=null;} }
    private static Message withoutCosmeticIds(Message m) {
        var builder=m.toBuilder();
        for(var entry:m.getAllFields().entrySet()) {
            var field=entry.getKey();
            if(field.getName().equals("identifier"))builder.clearField(field);
            else if(field.getJavaType()==FieldDescriptor.JavaType.MESSAGE){
                if(field.isRepeated()) for(int i=0;i<m.getRepeatedFieldCount(field);i++)
                    builder.setRepeatedField(field,i,withoutCosmeticIds((Message)m.getRepeatedField(field,i)));
                else builder.setField(field,withoutCosmeticIds((Message)entry.getValue()));
            }
        }
        return builder.build();
    }
    private static String nativeHash(FrameData d) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
            .digest(withoutCosmeticIds(d.toProto()).toByteArray()));
    }
    private static int mask(Key k){
        return (k.A?1:0)|(k.B?2:0)|(k.C?4:0)|(k.U?8:0)|(k.R?16:0)|(k.D?32:0)|(k.L?64:0);
    }
    private void record(Key[] keys) throws Exception {
        if(trace==null)return;
        final var d=nativeData();
        trace.write("{\"frame\":"+frame+",\"keyMasks\":["+(keys==null?0:mask(keys[0]))+","+(keys==null?0:mask(keys[1]))+"],\"nativeFrameSha256\":\""+nativeHash(d)+"\",\"p1\":"+fighter(d.getCharacter(true))+",\"p2\":"+fighter(d.getCharacter(false))+"}\n");
    }
    private final CommandCenter[] commands = {new CommandCenter(),new CommandCenter()};
    private FrameData nativeData() { return fight.createFrameData(Math.max(0, frame - 1), 1); }
    private boolean ko(FrameData data) { return data.getCharacter(true).getHp()<=0 || data.getCharacter(false).getHp()<=0; }
    private void initialize(int maxFrames, int hp, String p1, String p2) throws Exception {
        if(maxFrames<1||maxFrames>3600||hp<1||hp>400||!CHARS.contains(p1)||!CHARS.contains(p2))
            throw new IllegalArgumentException("invalid match defaults");
        FlagSetting.limitHpFlag=true;
        FlagSetting.muteFlag=true;
        FlagSetting.enableBuiltinSound=false;
        FlagSetting.enableReplaySound=false;
        FlagSetting.enableAudioPlayback=false;
        LaunchSetting.processingMode=LaunchSetting.HEADLESS_MODE;
        LaunchSetting.backgroundType=BackgroundType.GREY;
        LaunchSetting.maxHp=new int[]{hp,hp};
        LaunchSetting.characterNames=new String[]{p1,p2};
        LaunchSetting.aiNames=new String[]{"P1","P2"};
        GameSetting.ROUND_FRAME_NUMBER=maxFrames;
        GameSetting.ROUND_MAX=1;
        closeTrace();
        window="null";
        frames=maxFrames;
        frame=0;
        capture=null;
        captured=0;
        if(fight!=null)fight.close();
        for(var cmd:commands) cmd.skillCancel();
        // Original local resource loader; does not load audio in this configuration.
        GraphicManager.getInstance().setLetterFont(new LetterImage(new Font("SansSerif",Font.BOLD,24),true));
        ResourceLoader.getInstance().loadResource();
        fight=new Fighting();
        fight.initialize();
        fight.initRound();
    }
    private static String fighter(CharacterData x) {
        return String.format(Locale.ROOT,
          "{\"hp\":%d,\"energy\":%d,\"x\":%d,\"y\":%d,\"vx\":%d,\"vy\":%d,\"state\":\"%s\",\"action\":\"%s\",\"remainingActionFrames\":%d,\"isFront\":%b,\"canAct\":%b}",
          x.getHp(),x.getEnergy(),x.getCenterX(),x.getCenterY(),x.getSpeedX(),x.getSpeedY(),x.getState(),x.getAction(),x.getRemainingFrame(),x.isFront(),x.isControl());
    }
    private String describe() throws Exception {
        FrameData d=nativeData();
        var a=d.getCharacter(true);var b=d.getCharacter(false);
        final boolean ended=frame>=frames||ko(d);
        final String win=!ended?"pending":a.getHp()==b.getHp()?"tie":a.getHp()>b.getHp()?"p1":"p2";
        final String by=!ended?"pending":ko(d)?"ko":"time";
        final String sha=nativeHash(d);
        final String raw=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(d.toProto().toByteArray()));
        return "{\"ok\":true,\"frame\":"+frame+",\"framesLeft\":"+Math.max(0,frames-frame)+",\"nativeFrameSha256\":\""+sha+"\",\"rawNativeFrameSha256\":\""+raw+"\",\"p1\":"+fighter(a)+",\"p2\":"+fighter(b)+",\"terminated\":"+ended+",\"winner\":\""+win+"\",\"by\":\""+by+"\",\"lastWindow\":"+window+"}";
    }
    private void snap() throws Exception {
        if(capture==null)return;
        final FrameData d=nativeData();
        var gm=GraphicManager.getInstance();gm.resetScreen();
        ResourceDrawer.getInstance().drawResource(fight.getCharacters(),fight.getProjectileDeque(),
            fight.getHitEffectList(),Math.max(0, (int)(1000f*(frames-frame)/60)),1,true);
        ImageIO.write(gm.getScreenImage(),"png",capture.resolve(String.format("%06d.png",captured++)).toFile());
    }
    private void step(int count,String a,String b) throws Exception {
        if(count<1||count>600||!ALLOWED.contains(a)||!ALLOWED.contains(b))throw new IllegalArgumentException("invalid frame count or action");
        final String[] intents={a,b};
        final int start=frame;
        final int[] issued={0,0}, nonNeutral={0,0}, nativeAction={0,0};
        for(int k=0;k<count&&frame<frames&&!ko(nativeData());k++) {
            final FrameData d=nativeData();
            Key[] keys=new Key[2];
            for(int i=0;i<2;i++){
               final boolean p1=i==0;
               var cmd=commands[i];cmd.setFrameData(d,p1);
               if(!cmd.getSkillFlag()&&d.getCharacter(p1).isControl()&&!intents[i].equals("NEUTRAL")){
                   cmd.commandCall(intents[i]);
                   if(cmd.getSkillFlag())issued[i]++;
               }
               keys[i]=cmd.getSkillFlag()?cmd.getSkillKey():new Key();
               if(mask(keys[i])!=0)nonNeutral[i]++;
            }
            fight.processingFight(frame++,new KeyData(keys));
            final var after=nativeData();
            for(int i=0;i<2;i++) if(after.getCharacter(i==0).getAction().name().equals(intents[i]))nativeAction[i]++;
            record(keys);
            if(capture!=null&&frame%recordEvery==0)snap();
        }
        if(capture!=null&&frame>start&&(frame==frames||ko(nativeData()))&&frame%recordEvery!=0)snap();
        if(trace!=null)trace.flush();
        window=String.format(Locale.ROOT,
          "{\"fromFrame\":%d,\"requestedFrames\":%d,\"advancedFrames\":%d,\"tokens\":[\"%s\",\"%s\"],\"nativeQueuesIssued\":[%d,%d],\"nonNeutralInputFrames\":[%d,%d],\"matchingNativeActionFrames\":[%d,%d]}",
          start,count,frame-start,a,b,issued[0],issued[1],nonNeutral[0],nonNeutral[1],nativeAction[0],nativeAction[1]);
    }
    public static void main(String[] args) throws Exception {
        CupBridge b=new CupBridge();
        try(BufferedReader rd=new BufferedReader(new InputStreamReader(System.in))){
            for(String line;(line=rd.readLine())!=null;){
                if(line.isBlank())continue;
                String[] x=line.trim().split("\\s+");
                if(x[0].equals("quit"))break;
                try{
                    switch(x[0]){
                      case "new" -> b.initialize(Integer.parseInt(x[1]),Integer.parseInt(x[2]),x.length>3?x[3]:"ZEN",x.length>4?x[4]:"ZEN");
                      case "step" -> b.step(Integer.parseInt(x[1]),x[2],x[3]);
                      case "capture" -> {b.capture=Path.of(x[1]);b.recordEvery=Integer.parseInt(x[2]);if(b.recordEvery<1||b.recordEvery>12)throw new IllegalArgumentException("bad capture stride");Files.createDirectories(b.capture);b.snap();}
                      case "trace" -> {
                        b.closeTrace(); final var dest=Path.of(x[1]).toAbsolutePath();
                        Files.createDirectories(dest.getParent());
                        b.trace=Files.newBufferedWriter(dest); b.record(null); b.trace.flush();
                      }
                      case "observe" -> {}
                      default -> throw new IllegalArgumentException("unknown command");
                    }
                    System.out.println(b.describe());
                }catch(Exception e){System.out.println("{\"ok\":false,\"error\":\""+e.getClass().getSimpleName()+"\"}");e.printStackTrace(System.err);}
            }
        } finally {b.closeTrace();}
    }
}
